-- Example schema and queries to use with the client.
-- Copy/paste each statement into the client.

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, price) VALUES
  ('Keyboard', 199.90),
  ('Mouse', 79.90),
  ('Monitor', 1299.00);

SELECT * FROM products;

UPDATE products
SET price = 89.90
WHERE name = 'Mouse';

SELECT id, name, price FROM products WHERE price >= 100;

DELETE FROM products
WHERE name = 'Keyboard';

SELECT * FROM products;
