import os
import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from pymongo import MongoClient

load_dotenv()

# streamlit run d:/Code/Project-Dashboard-Template/app.py
# streamlit run app.py

# Postgres schema helper
PG_SCHEMA = os.getenv("PG_SCHEMA", "smart_kitchen")   # CHANGE: "public" to your own schema name
def qualify(sql: str) -> str:
    # Replace occurrences of {S}.<table> with <schema>.<table>
    return sql.replace("{S}.", f"{PG_SCHEMA}.")

# CONFIG: Postgres and Mongo Queries
CONFIG = {
    "postgres": {
        "enabled": True,
        "uri": os.getenv("PG_URI", "postgresql+psycopg2://postgres:password@localhost:5432/postgres"),
        "queries": {
            # User 1: RESTAURANT MANAGER
            "Manager: Restaurant Order Statistics (Table)": {
                "sql": """
                    WITH restaurant_orders AS (
                        -- Find orders processed by each restaurant
                        SELECT DISTINCT r.restaurant_id, o.order_id
                        FROM {S}.restaurants r
                        JOIN {S}.smart_kitchens sk ON r.restaurant_id = sk.restaurant_id
                        JOIN {S}.equipments e ON sk.kitchen_id = e.kitchen_id
                        JOIN {S}.cooking_records cr ON e.equipment_id = cr.equipment_id
                        JOIN {S}.orders o ON cr.order_id = o.order_id
                    ),
                    order_revenue AS (
                        -- Calculate revenue for each order
                        SELECT o.order_id, SUM(od.quantity * d.price) as revenue
                        FROM {S}.orders o
                        JOIN {S}.order_dishs od ON o.order_id = od.order_id
                        JOIN {S}.dishs d ON od.dish_id = d.dish_id
                        GROUP BY o.order_id
                    )
                    SELECT r.name AS restaurant_name,
                        COUNT(ro.order_id) AS total_orders,
                        COALESCE(SUM(orr.revenue), 0) AS total_revenue
                    FROM {S}.restaurants r
                    LEFT JOIN restaurant_orders ro ON r.restaurant_id = ro.restaurant_id
                    LEFT JOIN order_revenue orr ON ro.order_id = orr.order_id
                    GROUP BY r.restaurant_id, r.name
                    ORDER BY total_revenue DESC;
                """,
                "chart": {"type": "table"},
                "tags": ["manager"],
                "params": []
            },
            "Manager: Query the order record of a certain restaurant (Table)": {
                "sql": """
                    SELECT o.order_id,
                        o.order_time,
                        o.delivery_address,
                        u.name AS customer_name,
                        u.phone AS customer_phone,
                        o.payment_method
                    FROM {S}.orders o
                    JOIN {S}.users u ON o.user_id = u.user_id
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    JOIN {S}.dishs d ON od.dish_id = d.dish_id
                    JOIN {S}.cooking_records cr ON o.order_id = cr.order_id
                    JOIN {S}.equipments e ON cr.equipment_id = e.equipment_id
                    JOIN {S}.smart_kitchens sk ON e.kitchen_id = sk.kitchen_id
                    WHERE sk.restaurant_id = :restaurant_id
                    GROUP BY o.order_id, o.order_time, o.delivery_address, u.name, u.phone, o.payment_method
                    ORDER BY o.order_time DESC
                    LIMIT 100;
                """,
                "chart": {"type": "table"},
                "tags": ["manager"],
                "params": ["restaurant_id"]
            },
            "Manager: Dish Sales Ranking (Bar)": {
                "sql": """
                    SELECT d.dish_name, 
                           SUM(od.quantity) AS total_sold,
                           d.category
                    FROM {S}.dishs d
                    JOIN {S}.order_dishs od ON d.dish_id = od.dish_id
                    JOIN {S}.orders o ON od.order_id = o.order_id
                    WHERE o.order_time >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY d.dish_id, d.dish_name, d.category
                    ORDER BY total_sold DESC
                    LIMIT 10;
                """,
                "chart": {"type": "bar", "x": "dish_name", "y": "total_sold"},
                "tags": ["manager"],
                "params": []
            },
            "Manager: Payment Method Distribution (Pie)": {
                "sql": """
                    SELECT payment_method,
                        COUNT(*) AS order_count
                    FROM {S}.orders
                    GROUP BY payment_method
                    ORDER BY order_count DESC;
                """,
                "chart": {"type": "pie", "names": "payment_method", "values": "order_count"},
                "tags": ["manager"],
                "params": []
            },                                    

            # User 2: CHEF
            "Chef: Latest 20 Pending Dishes with Order and Restaurant Info (Table)": {
                "sql": """
                    SELECT DISTINCT o.order_id,
                        o.order_time,
                        r.name AS restaurant_name,
                        d.dish_name,
                        od.quantity,
                        d.standard_cook_time,
                        d.standard_cook_temp
                    FROM {S}.orders o
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    JOIN {S}.dishs d ON od.dish_id = d.dish_id
                    JOIN {S}.cooking_records cr ON o.order_id = cr.order_id AND od.dish_id = cr.dish_id
                    JOIN {S}.equipments e ON cr.equipment_id = e.equipment_id
                    JOIN {S}.smart_kitchens sk ON e.kitchen_id = sk.kitchen_id
                    JOIN {S}.restaurants r ON sk.restaurant_id = r.restaurant_id
                    WHERE r.restaurant_id = :restaurant_id
                        AND o.order_id NOT IN (
                            SELECT DISTINCT order_id FROM {S}.cooking_records 
                            WHERE start_time::date = CURRENT_DATE
                        )
                    ORDER BY o.order_time DESC
                    LIMIT 20;
                """,
                "chart": {"type": "table"},
                "tags": ["chef"],
                "params": ["restaurant_id"]
            },
            "Chef: Temperature Compliance Rate Statistics (Bar)": {
                "sql": """
                    SELECT d.dish_name, 
                        COUNT(*) AS total_cooks,
                        ROUND(SUM(CASE WHEN cr.temp_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS temp_compliance_rate
                    FROM {S}.cooking_records cr
                    JOIN {S}.dishs d ON cr.dish_id = d.dish_id
                    WHERE cr.start_time >= CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY d.dish_id, d.dish_name
                    HAVING COUNT(*) > 0
                    ORDER BY temp_compliance_rate ASC
                """,
                "chart": {"type": "bar", "x": "dish_name", "y": "temp_compliance_rate"},
                "tags": ["chef"],
                "params": ["days"]
            },
            "Chef: Time Compliance Rate Statistics (Bar)": {
                "sql": """
                    SELECT d.dish_name, 
                        COUNT(*) AS total_cooks,
                        ROUND(SUM(CASE WHEN cr.time_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS time_compliance_rate
                    FROM {S}.cooking_records cr
                    JOIN {S}.dishs d ON cr.dish_id = d.dish_id
                    WHERE cr.start_time >= CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY d.dish_id, d.dish_name
                    HAVING COUNT(*) > 0
                    ORDER BY time_compliance_rate ASC
                """,
                "chart": {"type": "bar", "x": "dish_name", "y": "time_compliance_rate"},
                "tags": ["chef"],
                "params": ["days"]
            },
            "Chef: Equipment Maintenance Reminder (Table)": {
                "sql": """
                    SELECT e.equipment_id,
                        sk.name AS kitchen_name,
                        e.production_date,
                        CASE WHEN COUNT(cr.record_id) > 1000 THEN 'Maintenance Required'
                                WHEN e.production_date < CURRENT_DATE - INTERVAL '3 years' THEN 'Aging Equipment'
                                ELSE 'Normal' END AS status
                    FROM {S}.equipments e
                    JOIN {S}.smart_kitchens sk ON e.kitchen_id = sk.kitchen_id
                    LEFT JOIN {S}.cooking_records cr ON e.equipment_id = cr.equipment_id
                    GROUP BY e.equipment_id, sk.name, e.production_date
                    HAVING COUNT(cr.record_id) > 1000 OR e.production_date < CURRENT_DATE - INTERVAL '3 years'
                    ORDER BY status, COUNT(cr.record_id) DESC;
                """,
                "chart": {"type": "table"},
                "tags": ["chef"],
                "params": []
            },

            # User 3: DELIVERY PERSON
            "Delivery: Latest Five Delivery Tasks (Table)": {
                "sql": """
                    SELECT o.order_id,
                        o.order_time,
                        o.delivery_address,
                        u.name AS customer_name,
                        u.phone AS customer_phone,
                        COUNT(od.dish_id) AS total_items
                    FROM {S}.orders o
                    JOIN {S}.users u ON o.user_id = u.user_id
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    WHERE o.delivery_id = :delivery_id
                    GROUP BY o.order_id, o.order_time, o.delivery_address, u.name, u.phone
                    ORDER BY o.order_time DESC
                    LIMIT 5;
                """,
                "chart": {"type": "table"},
                "tags": ["delivery"],
                "params": ["delivery_id"]
            },
            "Delivery: Top 5 Delivery Persons by Orders in Past Month (Bar)": {
                "sql": """
                    SELECT dp.name AS delivery_person,
                        COUNT(DISTINCT o.order_id) AS total_orders
                    FROM {S}.delivery_persons dp
                    JOIN {S}.orders o ON dp.delivery_id = o.delivery_id
                    WHERE o.order_time >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY dp.delivery_id, dp.name
                    ORDER BY total_orders DESC
                    LIMIT 5;
                """,
                "chart": {"type": "bar", "x": "delivery_person", "y": "total_orders"},
                "tags": ["delivery"],
                "params": []
            },
            "Delivery: All Delivery Records in Past Year (Table)": {
                "sql": """
                    SELECT o.order_id,
                        o.order_time,
                        o.delivery_address,
                        u.name AS customer_name,
                        u.phone AS customer_phone,
                        o.payment_method,
                        COUNT(od.dish_id) AS total_items,
                        SUM(od.quantity * d.price) AS total_amount
                    FROM {S}.orders o
                    JOIN {S}.users u ON o.user_id = u.user_id
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    JOIN {S}.dishs d ON od.dish_id = d.dish_id
                    WHERE o.delivery_id = :delivery_id
                    AND o.order_time >= CURRENT_DATE - INTERVAL '365 days'
                    GROUP BY o.order_id, o.order_time, o.delivery_address, u.name, u.phone, o.payment_method
                    ORDER BY o.order_time DESC
                    LIMIT 1000;
                """,
                "chart": {"type": "table"},
                "tags": ["delivery"],
                "params": ["delivery_id"]
            },

            # User 4: CUSTOMER
            "Customer: My Order History (Table)": {
                "sql": """
                    -- Some users have not placed any orders for dishes.
                    -- If "no rows" is displayed, you can try changing the value of user_id.
                    SELECT o.order_id,
                           o.order_time,
                           o.delivery_address,
                           o.payment_method,
                           SUM(od.quantity * d.price) AS total_amount
                    FROM {S}.orders o
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    JOIN {S}.dishs d ON od.dish_id = d.dish_id
                    WHERE o.user_id = :user_id
                    GROUP BY o.order_id, o.order_time, o.delivery_address, o.payment_method
                    ORDER BY o.order_time DESC
                    LIMIT 10;
                """,
                "chart": {"type": "table"},
                "tags": ["customer"],
                "params": ["user_id"]
            },
            "Customer: Most Ordered Dishes (Pie)": {
                "sql": """
                    SELECT d.dish_name,
                           SUM(od.quantity) AS times_ordered
                    FROM {S}.orders o
                    JOIN {S}.order_dishs od ON o.order_id = od.order_id
                    JOIN {S}.dishs d ON od.dish_id = d.dish_id
                    WHERE o.user_id = :user_id
                    GROUP BY d.dish_id, d.dish_name
                    ORDER BY times_ordered DESC
                    LIMIT 8;
                """,
                "chart": {"type": "pie", "names": "dish_name", "values": "times_ordered"},
                "tags": ["customer"],
                "params": ["user_id"]
            },
            "Customer: Price Distribution by Dish Category (Bar)": {
                "sql": """
                    SELECT category,
                        COUNT(*) AS dish_count,
                        ROUND(AVG(price), 2) AS avg_price,
                        ROUND(MIN(price), 2) AS min_price,
                        ROUND(MAX(price), 2) AS max_price
                    FROM {S}.dishs
                    GROUP BY category
                    ORDER BY avg_price DESC;
                """,
                "chart": {"type": "bar", "x": "category", "y": "avg_price"},
                "tags": ["customer"],
                "params": []
            },    
            "Customer: Dish Price Ranking (Table)": {
                "sql": """
                    SELECT dish_name,
                        price,
                        category
                    FROM {S}.dishs
                    ORDER BY price DESC;
                """,
                "chart": {"type": "table"},
                "tags": ["customer"],
                "params": []
            },                    

            # User 5: 
            "Quality: Dishes with a low temperature compliance rate (Table)": {
                "sql": """
                    SELECT d.dish_name,
                        COUNT(*) AS total_cooks,
                        ROUND(SUM(CASE WHEN cr.temp_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS compliance_rate
                    FROM {S}.cooking_records cr
                    JOIN {S}.dishs d ON cr.dish_id = d.dish_id
                    WHERE cr.start_time >= CURRENT_DATE - INTERVAL '1 day'
                    GROUP BY d.dish_id, d.dish_name
                    HAVING COUNT(*) > 0
                    ORDER BY compliance_rate ASC
                    LIMIT 5;
                """,
                "chart": {"type": "table"},
                "tags": ["quality"],
                "params": []
            },
            "Quality: Dishes with a low time compliance rate (Table)": {
                "sql": """
                    SELECT d.dish_name,
                        COUNT(*) AS total_cooks,
                        ROUND(SUM(CASE WHEN cr.time_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS compliance_rate
                    FROM {S}.cooking_records cr
                    JOIN {S}.dishs d ON cr.dish_id = d.dish_id
                    WHERE cr.start_time >= CURRENT_DATE - INTERVAL '1 day'
                    GROUP BY d.dish_id, d.dish_name
                    HAVING COUNT(*) > 0
                    ORDER BY compliance_rate ASC
                    LIMIT 5;
                """,
                "chart": {"type": "table"},
                "tags": ["quality"],
                "params": []
            },
            "Quality: Abnormal Cooking Record Analysis (Table)": {
                "sql": """
                    SELECT cr.record_id,
                        d.dish_name,
                        e.equipment_id,
                        cr.average_cook_temperature,
                        cr.temp_compliance,
                        cr.time_compliance,
                        cr.start_time
                    FROM {S}.cooking_records cr
                    JOIN {S}.dishs d ON cr.dish_id = d.dish_id
                    JOIN {S}.equipments e ON cr.equipment_id = e.equipment_id
                    WHERE cr.temp_compliance = 'No' OR cr.time_compliance = 'No'
                    ORDER BY cr.start_time DESC
                """,
                "chart": {"type": "table"},
                "tags": ["quality"],
                "params": []
            },
            "Quality: Dish Compliance Rate Comparison (Bar)": {
                "sql": """
                    SELECT d.dish_name,
                        ROUND(SUM(CASE WHEN cr.temp_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS temp_compliance_rate,
                        ROUND(SUM(CASE WHEN cr.time_compliance = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS time_compliance_rate
                    FROM {S}.dishs d
                    LEFT JOIN {S}.cooking_records cr ON d.dish_id = cr.dish_id
                    GROUP BY d.dish_id, d.dish_name
                    HAVING COUNT(*) > 0
                    ORDER BY temp_compliance_rate DESC
                """,
                "chart": {"type": "bar", "x": "dish_name", "y": ["temp_compliance_rate", "time_compliance_rate"]},
                "tags": ["quality"],
                "params": []
            }            
        }
    },

    "mongo": {
        "enabled": True,
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "db_name": os.getenv("MONGO_DB", "smartKitchen"),
    
        "queries": {
            "TS: Latest 20 Sensor Data Records (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$sort": {"ts": -1}},
                    {"$limit": 20},
                    {"$project": {
                        "_id": 0,
                        "Time": "$ts",
                        "Sensor ID": "$meta.sensor_id",
                        "Equipment ID": "$meta.equipment_id",
                        "Temperature(℃)": "$temperature_c",
                        "Humidity(%)": "$humidity_pct",
                        "Smoke Concentration": "$smoke_concentration.value",
                        "Status": "$status"
                    }}
                ],
                "chart": {"type": "table"}
            },

            "Telemetry: Current Temperature and Smoke Concentration for All Equipment (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$sort": {"ts": -1}},
                    {"$group": {
                        "_id": "$meta.equipment_id",
                        "Latest Time": {"$first": "$ts"},
                        "Temperature(℃)": {"$first": "$temperature_c"},
                        "Humidity(%)": {"$first": "$humidity_pct"},
                        "Smoke Concentration": {"$first": "$smoke_concentration.value"},
                        "Status": {"$first": "$status"}
                    }},
                    {"$sort": {"_id": 1}},
                    {"$project": {
                        "_id": 0,
                        "Equipment ID": "$_id",
                        "Latest Time": 1,
                        "Temperature(℃)": 1,
                        "Humidity(%)": 1,
                        "Smoke Concentration": 1,
                        "Status": 1
                    }}
                ],
                "chart": {"type": "table"}
            },

            "Telemetry: Sensor Failure Rate by Sensor (Bar)": {
                "collection": "sensor",
                "aggregate": [
                    {"$group": {
                        "_id": "$meta.sensor_id",
                        "total_records": {"$sum": 1},
                        "failure_records": {
                            "$sum": {
                                "$cond": [{"$ne": ["$status", "ok"]}, 1, 0]
                            }
                        }
                    }},
                    {"$project": {
                        "_id": 0,
                        "Sensor ID": "$_id",
                        "Total Records": "$total_records",
                        "Failure Records": "$failure_records",
                        "Failure Rate (%)": {
                            "$round": [
                                {"$multiply": [
                                    {"$divide": ["$failure_records", "$total_records"]},
                                    100
                                ]},
                                2
                            ]
                        }
                    }},
                    {"$match": {
                        "Total Records": {"$gt": 0}
                    }},
                    {"$sort": {"Failure Rate (%)": -1}},
                    # {"$limit": 20}
                ],
                "chart": {"type": "bar", "x": "Sensor ID", "y": "Failure Rate (%)"}
            },            

            "TS: Equipment with Current High Temperature (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$sort": {"ts": -1}},
                    {"$group": {
                        "_id": "$meta.equipment_id",
                        "Latest Time": {"$first": "$ts"},
                        "Temperature(℃)": {"$first": "$temperature_c"},
                        "Humidity(%)": {"$first": "$humidity_pct"},
                        "Smoke Concentration": {"$first": "$smoke_concentration.value"},
                        "Status": {"$first": "$status"}
                    }},
                    {"$match": {
                        "Temperature(℃)": {"$gt": 100}
                    }},
                    {"$sort": {"Temperature(℃)": -1}},
                    {"$project": {
                        "_id": 0,
                        "Equipment ID": "$_id",
                        "Latest Time": 1,
                        "Temperature(℃)": 1,
                        "Humidity(%)": 1,
                        "Smoke Concentration": 1,
                        "Status": 1
                    }}
                ],
                "chart": {"type": "table"}
            },

            "TS: Equipment with Current High Smoke Concentration (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$sort": {"ts": -1}},
                    {"$group": {
                        "_id": "$meta.equipment_id",
                        "Latest Time": {"$first": "$ts"},
                        "Temperature(℃)": {"$first": "$temperature_c"},
                        "Humidity(%)": {"$first": "$humidity_pct"},
                        "Smoke Concentration": {"$first": "$smoke_concentration.value"},
                        "Status": {"$first": "$status"}
                    }},
                    {"$match": {
                        "Smoke Concentration": {"$gt": 800}
                    }},
                    {"$sort": {"Smoke Concentration": -1}},
                    {"$project": {
                        "_id": 0,
                        "Equipment ID": "$_id",
                        "Latest Time": 1,
                        "Temperature(℃)": 1,
                        "Humidity(%)": 1,
                        "Smoke Concentration": 1,
                        "Status": 1
                    }}
                ],
                "chart": {"type": "table"}
            },            
                        
            "TS: Current Sensor Status Monitoring (Pie)": {
                "collection": "sensor",
                "aggregate": [
                    {"$sort": {"ts": -1}},
                    {"$group": {
                        "_id": "$meta.sensor_id",
                        "Latest Status": {"$first": "$status"},
                        "Last Update Time": {"$first": "$ts"}
                    }},
                    {"$group": {
                        "_id": "$Latest Status",
                        "Sensor Count": {"$count": {}}
                    }}
                ],
                "chart": {"type": "pie", "names": "_id", "values": "Sensor Count"}
            },

            "Telemetry: Data Volume Statistics by Equipment (Bar)": {
                "collection": "sensor",
                "aggregate": [
                    {"$group": {
                        "_id": "$meta.equipment_id",
                        "Data Volume": {"$count": {}}
                    }},
                    {"$sort": {"Data Volume": -1}}
                ],
                "chart": {"type": "bar", "x": "_id", "y": "Data Volume"}
            },

            "Telemetry: Equipment Status Anomaly Records (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$match": {
                        "status": {"$ne": "ok"}
                    }},
                    {"$project": {
                        "_id": 0,
                        "Time": "$ts",
                        "Equipment ID": "$meta.equipment_id",
                        "Sensor ID": "$meta.sensor_id",
                        "Status": "$status"
                    }},
                    {"$sort": {"Time": -1}}
                ],
                "chart": {"type": "table"}
            },

            "Telemetry: Average Sensor Readings (Table)": {
                "collection": "sensor",
                "aggregate": [
                    {"$group": {
                        "_id": None,
                        "Average Temperature": {"$avg": "$temperature_c"},
                        "Average Humidity": {"$avg": "$humidity_pct"},
                        "Average Smoke Concentration": {"$avg": "$smoke_concentration.value"},
                        "Record Count": {"$count": {}}
                    }},
                    {"$project": {
                        "_id": 0,
                        "Average Temperature": {"$round": ["$Average Temperature", 1]},
                        "Average Humidity": {"$round": ["$Average Humidity", 1]},
                        "Average Smoke Concentration": {"$round": ["$Average Smoke Concentration", 1]},
                        "Record Count": 1
                    }}
                ],
                "chart": {"type": "table"}
            }       
        }
    }    
}

# The following block of code will create a simple Streamlit dashboard page
st.set_page_config(page_title="Smart Kitchen DB Dashboard", layout="wide")
st.title("Smart Kitchen | Mini Dashboard (Postgres + MongoDB)")

def metric_row(metrics: dict):
    cols = st.columns(len(metrics))
    for (k, v), c in zip(metrics.items(), cols):
        c.metric(k, v)

@st.cache_resource
def get_pg_engine(uri: str):
    return create_engine(uri, pool_pre_ping=True, future=True)

@st.cache_data(ttl=60)
def run_pg_query(_engine, sql: str, params: dict | None = None):
    import pandas as pd
    with _engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

#@st.cache_data(ttl=60)
#def run_pg_query(_engine, sql: str, params: dict | None = None, enc: str = None):
#    import pandas as pd
#    with _engine.connect() as conn:
#        if enc:
#            conn.exec_driver_sql(f"SET client_encoding TO '{enc}'")
#        return pd.read_sql(text(sql), conn, params=params or {})

@st.cache_resource
def get_mongo_client(uri: str):
    return MongoClient(uri)

def mongo_overview(client: MongoClient, db_name: str):
    info = client.server_info()
    db = client[db_name]
    colls = db.list_collection_names()
    stats = db.command("dbstats")
    total_docs = sum(db[c].estimated_document_count() for c in colls) if colls else 0
    return {
        "DB": db_name,
        "Collections": f"{len(colls):,}",
        "Total docs (est.)": f"{total_docs:,}",
        "Storage": f"{round(stats.get('storageSize',0)/1024/1024,1)} MB",
        "Version": info.get("version", "unknown")
    }

@st.cache_data(ttl=60)
def run_mongo_aggregate(_client, db_name: str, coll: str, stages: list):
    db = _client[db_name]
    docs = list(db[coll].aggregate(stages, allowDiskUse=True))
    return pd.json_normalize(docs) if docs else pd.DataFrame()

def render_chart(df: pd.DataFrame, spec: dict):
    if df.empty:
        st.info("No rows.")
        return
    ctype = spec.get("type", "table")
    # light datetime parsing for x axes
    for c in df.columns:
        if df[c].dtype == "object":
            try:
                df[c] = pd.to_datetime(df[c])
            except Exception:
                pass

    if ctype == "table":
        st.dataframe(df, use_container_width=True)
    elif ctype == "line":
        st.plotly_chart(px.line(df, x=spec["x"], y=spec["y"]), use_container_width=True)
    elif ctype == "bar":
        st.plotly_chart(px.bar(df, x=spec["x"], y=spec["y"]), use_container_width=True)
    elif ctype == "pie":
        st.plotly_chart(px.pie(df, names=spec["names"], values=spec["values"]), use_container_width=True)
    elif ctype == "heatmap":
        pivot = pd.pivot_table(df, index=spec["rows"], columns=spec["cols"], values=spec["values"], aggfunc="mean")
        st.plotly_chart(px.imshow(pivot, aspect="auto", origin="upper",
                                  labels=dict(x=spec["cols"], y=spec["rows"], color=spec["values"])),
                        use_container_width=True)
    elif ctype == "treemap":
        st.plotly_chart(px.treemap(df, path=spec["path"], values=spec["values"]), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

with st.sidebar:
    st.header("Connections")
    pg_uri = st.text_input("Postgres URI", CONFIG["postgres"]["uri"])     
    mongo_uri = st.text_input("Mongo URI", CONFIG["mongo"]["uri"])        
    mongo_db = st.text_input("Mongo DB name", CONFIG["mongo"]["db_name"]) 
    st.divider()
    auto_run = st.checkbox("Auto-run on selection change", value=False, key="auto_run_global")

    st.header("Role & Parameters")
    # Postgres
    st.subheader("Postgres parameters")
    role = st.selectbox("User role", ["manager", "chef", "delivery", "customer", "quality", "all"], index=5)
    user_id = st.number_input("user_id", min_value=1, value=1, step=1)
    delivery_id = st.number_input("delivery_id", min_value=1, value=1, step=1)
    restaurant_id = st.number_input("restaurant_id", min_value=1, value=1, step=1)
    # kitchen_id = st.number_input("kitchen_id", min_value=1, value=1, step=1)
    days = st.slider("last N days", 1, 365, 7)
    
    # MongoDB
    # st.subheader("MongoDB parameters")
    # equipment_id = st.text_input("equipment_id", value="E079")
    # sensor_id = st.text_input("sensor_id", value="aq-001-1")
    

    PARAMS_CTX = {
        "user_id": int(user_id),
        "delivery_id": int(delivery_id),
        "restaurant_id": int(restaurant_id),
        # "kitchen_id": int(kitchen_id),
        "days": int(days),
        # "equipment_id": equipment_id,
        # "sensor_id": sensor_id
    } 

#Postgres part of the dashboard
st.subheader("Postgres")

try:
    
    eng = get_pg_engine(pg_uri)
    with st.expander("Run Postgres query", expanded=True):
        # The following will filter queries by role
        def filter_queries_by_role(qdict: dict, role: str) -> dict:
            def ok(tags):
                t = [s.lower() for s in (tags or ["all"])]
                return "all" in t or role.lower() in t
            return {name: q for name, q in qdict.items() if ok(q.get("tags"))}

        pg_all = CONFIG["postgres"]["queries"]
        pg_q = filter_queries_by_role(pg_all, role)

        names = list(pg_q.keys()) or ["(no queries for this role)"]
        sel = st.selectbox("Choose a saved query", names, key="pg_sel")

        if sel in pg_q:
            q = pg_q[sel]
            sql = qualify(q["sql"])   
            st.code(sql, language="sql")

            run  = auto_run or st.button("▶ Run Postgres", key="pg_run")
            if run:
                wanted = q.get("params", [])
                params = {k: PARAMS_CTX[k] for k in wanted}
                df = run_pg_query(eng, sql, params=params)
                render_chart(df, q["chart"])
            #if run:
            #    wanted = q.get("params", [])
            #    params = {k: PARAMS_CTX[k] for k in wanted}
            #    df = run_pg_query(eng, sql, params=params, enc=os.getenv("PG_CLIENT_ENCODING", "UTF8"))
            #    render_chart(df, q["chart"])            
        else:
            st.info("No Postgres queries tagged for this role.")
except Exception as e:
    st.error(f"Postgres error: {e}")

# Mongo panel
if CONFIG["mongo"]["enabled"]:
    st.subheader("🍃 MongoDB")
    try:
        mongo_client = get_mongo_client(mongo_uri)   
        metric_row(mongo_overview(mongo_client, mongo_db))

        with st.expander("Run Mongo aggregation", expanded=True):
            mongo_query_names = list(CONFIG["mongo"]["queries"].keys())
            selm = st.selectbox("Choose a saved aggregation", mongo_query_names, key="mongo_sel")
            q = CONFIG["mongo"]["queries"][selm]
            st.write(f"**Collection:** `{q['collection']}`")
            st.code(str(q["aggregate"]), language="python")
            runm = auto_run or st.button("▶ Run Mongo", key="mongo_run")
            if runm:
                dfm = run_mongo_aggregate(mongo_client, mongo_db, q["collection"], q["aggregate"])
                render_chart(dfm, q["chart"])
    except Exception as e:
        st.error(f"Mongo error: {e}")
