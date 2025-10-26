SET search_path TO smart_kitchen;

CREATE TABLE restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    restaurant_address TEXT NOT NULL,
	restaurant_contact VARCHAR(254) NOT NULL
);

CREATE TABLE smart_kitchens (
    kitchen_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    floor CHAR(1) NOT NULL,
	restaurant_id INT REFERENCES restaurants(restaurant_id)
);

CREATE TABLE equipments (
    equipment_id SERIAL PRIMARY KEY,
    production_date DATE NOT NULL,
	kitchen_id INT REFERENCES smart_kitchens(kitchen_id)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
	phone VARCHAR(20) NOT NULL,
	default_address TEXT NOT NULL,
	register_time DATE NOT NULL
);

CREATE TABLE dishs(
	dish_id SERIAL PRIMARY KEY,
	dish_name TEXT NOT NULL,
	standard_cook_time VARCHAR(10) NOT NULL,
	standard_cook_temp VARCHAR(10) NOT NULL,
	price DECIMAL(10,2) NOT NULL,
	category TEXT NOT NULL CHECK (category IN ('Appetizer', 'Staple Food','Dessert','Drink'))
);

CREATE TABLE sensors(
	sensor_id SERIAL PRIMARY KEY,
	equipment_id INT REFERENCES equipments(equipment_id)
);

CREATE TABLE delivery_persons(
	delivery_id SERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	phone VARCHAR(20) NOT NULL,
	status TEXT NOT NULL CHECK (status IN('Available','Busy'))
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
	order_time TIMESTAMP NOT NULL,
	delivery_address TEXT NOT NULL,
	payment_method TEXT NOT NULL,
	user_id INT REFERENCES users(user_id),
	delivery_id INT REFERENCES delivery_persons(delivery_id)
);

CREATE TABLE cooking_records(
	record_id SERIAL PRIMARY KEY,
	order_id INT REFERENCES orders(order_id),
	dish_id INT REFERENCES dishs(dish_id),
	equipment_id INT REFERENCES equipments(equipment_id),
	average_cook_temperature VARCHAR(20) NOT NULL,
	start_time TIMESTAMP NOT NULL,
	end_time TIMESTAMP NOT NULL,
	temp_compliance TEXT NOT NULL,
	time_compliance TEXT NOT NULL
);

CREATE TABLE order_dishs (
	order_id INT REFERENCES orders(order_id),
	dish_id INT REFERENCES dishs(dish_id),
   	quantity INT NOT NULL,
    PRIMARY KEY (order_id, dish_id)
);


-- 1. Insert 5 restaurants
INSERT INTO restaurants (name, restaurant_address, restaurant_contact) VALUES
('Gourmet Haven', '123 Main St, Foodville', 'contact@gourmethaven.com'),
('Urban Bites', '456 Oak Ave, Culinary City', 'info@urbanbites.com'),
('Seaside Grill', '789 Beach Blvd, Coastaltown', 'seaside@grill.com'),
('Mountain View Eats', '321 Pine Rd, Highlands', 'contact@mountainview.com'),
('Golden Wok', '654 Bamboo Ln, Chinatown', 'goldenwok@mail.com');

-- 2. Insert 12 kitchens (distributed across 5 restaurants)
INSERT INTO smart_kitchens (name, floor, restaurant_id) VALUES
('Main Kitchen', '1', 1), ('Banquet Kitchen', '2', 1),
('Express Kitchen', '1', 2), ('Catering Kitchen', 'B', 2),
('Ocean View Kitchen', '1', 3), ('Patio Kitchen', 'G', 3),
('Alpine Kitchen', '1', 4), ('Summit Kitchen', '3', 4),
('Dragon Kitchen', '1', 5), ('Phoenix Kitchen', '2', 5),
('Festival Kitchen', '1', 1), ('Garden Kitchen', '2', 3);

-- 3. Insert 20 equipments (assigned to specific kitchens)
INSERT INTO equipments (production_date, kitchen_id) VALUES
-- Restaurant 1 (3 kitchens)
('2022-01-15', 1), ('2022-03-10', 1), ('2022-05-20', 1), 
('2022-07-05', 2), ('2022-09-12', 2),
('2022-11-30', 3),
-- Restaurant 2 (2 kitchens)
('2021-11-30', 4), ('2022-02-14', 4), 
('2022-04-18', 5), ('2022-06-22', 5),
-- Restaurant 3 (3 kitchens)
('2020-09-12', 6), ('2021-01-25', 6), 
('2021-03-30', 7), ('2021-05-15', 7),
('2021-07-20', 8),
-- Restaurant 4 (2 kitchens)
('2023-02-10', 9), ('2023-04-05', 9),
('2023-06-20', 10),
-- Restaurant 5 (2 kitchens)
('2022-09-01', 11), ('2022-11-11', 11),
('2023-01-20', 12);

-- 4. Insert 40 sensors (2 per equipment)
INSERT INTO sensors (equipment_id) VALUES
(1),(1),(2),(2),(3),(3),(4),(4),(5),(5),
(6),(6),(7),(7),(8),(8),(9),(9),(10),(10),
(11),(11),(12),(12),(13),(13),(14),(14),(15),(15),
(16),(16),(17),(17),(18),(18),(19),(19),(20),(20);

-- 5. Insert 50 dishes
INSERT INTO dishs (dish_name, standard_cook_time, standard_cook_temp, price, category) VALUES
-- Appetizers (10)
('Spring Rolls', '8', '180°C', 5.99, 'Appetizer'),
('Bruschetta', '6', '200°C', 6.50, 'Appetizer'),
('Calamari', '10', '190°C', 8.99, 'Appetizer'),
('Garlic Bread', '5', '180°C', 4.50, 'Appetizer'),
('Stuffed Mushrooms', '12', '175°C', 7.99, 'Appetizer'),
('Chicken Wings', '15', '185°C', 9.50, 'Appetizer'),
('Shrimp Cocktail', '0', '0°C', 10.99, 'Appetizer'),
('Nachos', '7', '200°C', 8.50, 'Appetizer'),
('Mozzarella Sticks', '9', '190°C', 7.50, 'Appetizer'),
('Edamame', '5', '100°C', 4.99, 'Appetizer'),

-- Staple Foods (25)
('Spaghetti Carbonara', '15', '100°C', 12.99, 'Staple Food'),
('Beef Burger', '12', '200°C', 11.50, 'Staple Food'),
('Chicken Curry', '20', '180°C', 13.99, 'Staple Food'),
('Vegetable Stir Fry', '10', '220°C', 10.99, 'Staple Food'),
('Margherita Pizza', '18', '250°C', 14.50, 'Staple Food'),
('Fish and Chips', '15', '190°C', 16.99, 'Staple Food'),
('Beef Tacos', '10', '180°C', 11.99, 'Staple Food'),
('Chicken Parmesan', '22', '200°C', 15.50, 'Staple Food'),
('Vegetable Lasagna', '25', '180°C', 13.50, 'Staple Food'),
('BBQ Ribs', '30', '175°C', 18.99, 'Staple Food'),
('Sushi Platter', '0', '0°C', 22.50, 'Staple Food'),
('Pad Thai', '12', '220°C', 12.99, 'Staple Food'),
('Beef Pho', '15', '100°C', 14.50, 'Staple Food'),
('Chicken Quesadilla', '10', '200°C', 10.99, 'Staple Food'),
('Mushroom Risotto', '20', '180°C', 13.99, 'Staple Food'),
('Grilled Salmon', '15', '200°C', 19.99, 'Staple Food'),
('Pork Schnitzel', '18', '190°C', 16.50, 'Staple Food'),
('Vegetable Biryani', '25', '180°C', 12.99, 'Staple Food'),
('Beef Burrito', '12', '200°C', 11.50, 'Staple Food'),
('Chicken Shawarma', '15', '220°C', 12.99, 'Staple Food'),
('Vegetable Paella', '30', '180°C', 17.50, 'Staple Food'),
('Beef Lasagna', '28', '180°C', 16.99, 'Staple Food'),
('Chicken Fajitas', '18', '220°C', 15.50, 'Staple Food'),
('Tofu Curry', '20', '180°C', 11.99, 'Staple Food'),
('Lamb Chops', '22', '200°C', 24.99, 'Staple Food'),

-- Desserts (10)
('Chocolate Cake', '25', '180°C', 7.99, 'Dessert'),
('Cheesecake', '0', '0°C', 8.50, 'Dessert'),
('Apple Pie', '30', '190°C', 6.99, 'Dessert'),
('Tiramisu', '0', '0°C', 9.50, 'Dessert'),
('Creme Brulee', '0', '0°C', 7.50, 'Dessert'),
('Ice Cream Sundae', '0', '0°C', 6.99, 'Dessert'),
('Fruit Tart', '0', '0°C', 7.99, 'Dessert'),
('Chocolate Mousse', '0', '0°C', 6.50, 'Dessert'),
('Panna Cotta', '0', '0°C', 7.50, 'Dessert'),
('Baklava', '0', '0°C', 5.99, 'Dessert'),

-- Drinks (5)
('Fresh Lemonade', '0', '0°C', 3.99, 'Drink'),
('Iced Tea', '0', '0°C', 3.50, 'Drink'),
('Soda', '0', '0°C', 2.99, 'Drink'),
('Fresh Juice', '0', '0°C', 4.50, 'Drink'),
('Milkshake', '0', '0°C', 5.99, 'Drink');

-- 6. Insert 200 users (fixed phone number generation)
INSERT INTO users (name, phone, default_address, register_time)
SELECT 
  'User_' || id,
  '1-' || 
  LPAD((FLOOR(RANDOM()*899)+100)::TEXT, 3, '0') || '-' ||
  LPAD((FLOOR(RANDOM()*899)+100)::TEXT, 3, '0') || '-' ||
  LPAD((FLOOR(RANDOM()*8999)+1000)::TEXT, 4, '0'),
  (ARRAY['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr'])[FLOOR(RANDOM()*5)+1] || ', ' || 
  (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'])[FLOOR(RANDOM()*5)+1],
  CURRENT_DATE - (FLOOR(RANDOM()*365) || ' days')::INTERVAL
FROM generate_series(1,200) id;

-- 7. Insert 30 delivery persons (fixed phone number generation)
INSERT INTO delivery_persons (name, phone, status)
SELECT 
  'Driver_' || id,
  '1-' || 
  LPAD((FLOOR(RANDOM()*899)+100)::TEXT, 3, '0') || '-' ||
  LPAD((FLOOR(RANDOM()*899)+100)::TEXT, 3, '0') || '-' ||
  LPAD((FLOOR(RANDOM()*8999)+1000)::TEXT, 4, '0'),
  (ARRAY['Available','Busy'])[FLOOR(RANDOM()*2)+1]
FROM generate_series(1,30) id;

-- 8. Insert 500 orders (ensure each restaurant has orders, each delivery person has orders)
WITH all_delivery_persons AS (
  SELECT delivery_id FROM delivery_persons
),
delivery_orders_base AS (
  -- Ensure each delivery person has at least one order
  SELECT 
    dp.delivery_id,
    r.restaurant_id,
    u.user_id
  FROM all_delivery_persons dp
  CROSS JOIN restaurants r
  CROSS JOIN (SELECT user_id FROM users ORDER BY RANDOM() LIMIT 1) u
  ORDER BY RANDOM()
),
delivery_orders AS (
  -- Assign one order to each delivery person
  SELECT DISTINCT ON (dp.delivery_id)
    dp.delivery_id,
    r.restaurant_id,
    u.user_id
  FROM all_delivery_persons dp
  CROSS JOIN restaurants r
  CROSS JOIN (SELECT user_id FROM users ORDER BY RANDOM() LIMIT 1) u
  ORDER BY dp.delivery_id, RANDOM()
),
remaining_orders AS (
  -- Randomly assign remaining orders
  SELECT 
    r.restaurant_id,
    u.user_id,
    dp.delivery_id
  FROM restaurants r
  CROSS JOIN (SELECT user_id FROM users ORDER BY RANDOM() LIMIT 100) u
  CROSS JOIN (SELECT delivery_id FROM delivery_persons ORDER BY RANDOM()) dp
  ORDER BY RANDOM()
  LIMIT 500 - (SELECT COUNT(*) FROM delivery_orders)
),
combined_orders AS (
  SELECT restaurant_id, user_id, delivery_id FROM delivery_orders
  UNION ALL
  SELECT restaurant_id, user_id, delivery_id FROM remaining_orders
),
restaurant_orders AS (
  SELECT 
    restaurant_id,
    user_id,
    delivery_id
  FROM combined_orders
  ORDER BY RANDOM()
  LIMIT 500
)
INSERT INTO orders (order_time, delivery_address, payment_method, user_id, delivery_id)
SELECT 
  TIMESTAMP '2025-10-01' + 
    (RANDOM() * EXTRACT(EPOCH FROM (TIMESTAMP '2025-12-01' - TIMESTAMP '2025-10-01'))) * INTERVAL '1 second',
  (SELECT default_address FROM users WHERE user_id = ro.user_id),
  (ARRAY['Credit Card','Cash','PayPal','Apple Pay'])[FLOOR(RANDOM()*4)+1],
  ro.user_id,
  ro.delivery_id
FROM restaurant_orders ro;

-- 9. Insert order dishes (1-5 dishes per order, 1-3 portions per dish)
WITH order_restaurant AS (
  SELECT 
    o.order_id,
    (o.order_id % 5) + 1 AS restaurant_id
  FROM orders o
),
dish_numbers AS (
  -- Assign a sequence number to each dish
  SELECT 
    dish_id,
    ROW_NUMBER() OVER (ORDER BY dish_id) as dish_num
  FROM dishs
  WHERE category != 'Drink'
),
order_dish_selections AS (
  SELECT 
    ord.order_id,
    dn.dish_id,
    FLOOR(RANDOM()*3)+1 AS quantity,
    -- Create a more random selection pattern using order ID and dish sequence number
    (ord.order_id * 97 + dn.dish_num * 31) % 47 as selection_score
  FROM order_restaurant ord
  CROSS JOIN dish_numbers dn
  WHERE dn.dish_num <= 45  -- Limit dish range
),
filtered_selections AS (
  SELECT 
    order_id,
    dish_id,
    quantity,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY selection_score) as rn
  FROM order_dish_selections
),
order_dish_counts AS (
  SELECT 
    order_id,
    FLOOR(RANDOM()*5)+1 as dish_count
  FROM orders
)
INSERT INTO order_dishs (order_id, dish_id, quantity)
SELECT 
  fs.order_id,
  fs.dish_id,
  fs.quantity
FROM filtered_selections fs
JOIN order_dish_counts odc ON fs.order_id = odc.order_id
WHERE fs.rn <= odc.dish_count
AND NOT EXISTS (
  SELECT 1 FROM order_dishs od 
  WHERE od.order_id = fs.order_id AND od.dish_id = fs.dish_id
);

-- 10. Insert cooking records (one record per dish portion, except drinks)
WITH order_restaurant_mapping AS (
  SELECT DISTINCT
    o.order_id,
    (o.order_id % 5) + 1 AS restaurant_id
  FROM orders o
  JOIN order_dishs od ON o.order_id = od.order_id
),
order_equipment_mapping AS (
  SELECT DISTINCT
    orm.order_id,
    orm.restaurant_id,
    e.equipment_id
  FROM order_restaurant_mapping orm
  JOIN smart_kitchens k ON orm.restaurant_id = k.restaurant_id
  JOIN equipments e ON k.kitchen_id = e.kitchen_id
  WHERE e.equipment_id IS NOT NULL
),
cooking_records_data AS (
  SELECT 
    od.order_id,
    od.dish_id,
    oem.equipment_id,
    -- Generate reasonable cooking temperature (within ±10% of standard temperature)
    CASE 
      WHEN d.standard_cook_temp != '0°C' THEN 
        ROUND((SPLIT_PART(d.standard_cook_temp, '°', 1)::NUMERIC * (0.9 + RANDOM()*0.2))::NUMERIC, 1) || '°C'
      ELSE '0°C'
    END AS average_cook_temperature,
    -- Start time: 0-30 minutes after order time
    o.order_time + (RANDOM() * 30 || ' minutes')::INTERVAL AS start_time,
    -- End time: Start time + standard cooking time (±20%)
    o.order_time + (RANDOM() * 30 || ' minutes')::INTERVAL + 
      (CASE 
        WHEN d.standard_cook_time != '0' THEN 
          (SPLIT_PART(d.standard_cook_time, ' ', 1)::NUMERIC * (0.8 + RANDOM()*0.4) || ' minutes')::INTERVAL
        ELSE '0 minutes'::INTERVAL
      END) AS end_time,
    -- Temperature compliance (90% compliance rate)
    CASE WHEN RANDOM() > 0.1 THEN 'Yes' ELSE 'No' END AS temp_compliance,
    -- Time compliance (85% compliance rate)
    CASE WHEN RANDOM() > 0.15 THEN 'Yes' ELSE 'No' END AS time_compliance,
    od.quantity
  FROM order_dishs od
  JOIN orders o ON od.order_id = o.order_id
  JOIN dishs d ON od.dish_id = d.dish_id
  JOIN order_equipment_mapping oem ON od.order_id = oem.order_id
  WHERE d.category != 'Drink' -- Drinks have no cooking records
    AND NOT EXISTS (
      SELECT 1 FROM cooking_records cr 
      WHERE cr.order_id = od.order_id AND cr.dish_id = od.dish_id
    )
)
INSERT INTO cooking_records (order_id, dish_id, equipment_id, average_cook_temperature, start_time, end_time, temp_compliance, time_compliance)
SELECT 
  order_id,
  dish_id,
  equipment_id,
  average_cook_temperature,
  start_time,
  end_time,
  temp_compliance,
  time_compliance
FROM cooking_records_data
CROSS JOIN generate_series(1, cooking_records_data.quantity);

-- Additional: Add drinks to some orders (no cooking records)
WITH drink_orders_base AS (
  SELECT DISTINCT o.order_id
  FROM orders o
),
random_drink_orders AS (
  SELECT order_id
  FROM drink_orders_base
  ORDER BY RANDOM()
  LIMIT 200
),
drink_data AS (
  SELECT 
    rdo.order_id,
    d.dish_id,
    FLOOR(RANDOM()*2)+1 AS quantity
  FROM random_drink_orders rdo
  CROSS JOIN dishs d
  WHERE d.category = 'Drink'
    AND NOT EXISTS (
      SELECT 1 FROM order_dishs od 
      WHERE od.order_id = rdo.order_id AND od.dish_id = d.dish_id
    )
)
INSERT INTO order_dishs (order_id, dish_id, quantity)
SELECT order_id, dish_id, quantity
FROM drink_data
ORDER BY RANDOM()
LIMIT 300;
