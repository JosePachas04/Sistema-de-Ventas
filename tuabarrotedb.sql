USE tuabarrotedb;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'customer';

INSERT INTO users (username, password) VALUES
('admin', 'scrypt:32768:8:1$9kTRyGVS9v7fr7br$eca122803370911720e14a6c9dfc95a35cd6e702938fbac645d85c2754a265fb64ad3a49bce420a09a67e37810c85abcd90cfbfee199d18610ce7fb5acea0de8');

UPDATE users
SET role = 'admin'
WHERE username = 'admin';

SELECT id, username, role FROM users;
SELECT * FROM users;

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT, -- Descripción opcional de la categoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE products
ADD COLUMN image_filename VARCHAR(255) NULL;

ALTER TABLE products
ADD COLUMN category_id INT NULL;

ALTER TABLE products
ADD CONSTRAINT fk_product_category
FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

INSERT INTO categories (name) VALUES
('Frutas y verduras'),
('Carnes y mariscos'),
('Desayuno y lácteos'),
('Panadería'),
('Bebidas'),
('Alimentos congelados'),
('Galletas y snacks'),
('Comestibles y productos básicos'),
('Necesidades del hogar'),
('Cuidado de la salud'),
('Bebé y embarazo');

SELECT * FROM categories;

INSERT INTO products (name, price, stock, category_id, is_active, description) VALUES
('Plátano de Isla', 3.50, 50, 1, TRUE, 'Precio por kg.'),
('Papa Canchán', 2.00, 100, 1, TRUE, 'Precio por kg.'),
('Tomate Italiano', 2.80, 80, 1, TRUE, 'Precio por kg.'),

('Pollo entero', 9.50, 30, 2, TRUE, 'Precio por kg.'),
('Filete de pescado (merluza)', 14.00, 20, 2, TRUE, 'Precio por kg.'),
('Carne molida de res', 16.00, 25, 2, TRUE, 'Precio por kg.'),

('Leche Gloria evaporada 400 g', 4.00, 60, 3, TRUE, NULL), -- Deja description como NULL si no hay
('Pan de molde Bimbo 500 g', 7.00, 40, 3, TRUE, NULL),
('Queso fresco artesanal', 12.00, 15, 3, TRUE, 'Precio por kg.'),

('Pan francés', 0.30, 200, 4, TRUE, 'Precio por unidad.'),
('Pan integral artesanal', 1.20, 50, 4, TRUE, 'Precio por unidad.'),
('Rosquitas andinas', 4.50, 35, 4, TRUE, 'Por bolsa.'),

('Inca Kola 1.5 L', 5.00, 80, 5, TRUE, NULL),
('Refresco Cifrut 500 ml', 2.00, 120, 5, TRUE, NULL),
('Agua San Luis 2.5 L', 3.80, 90, 5, TRUE, NULL),

('Papas fritas precocidas 1 kg', 9.00, 25, 6, TRUE, NULL),
('Nuggets de pollo', 12.00, 30, 6, TRUE, 'Precio por 500 g.'),
('Empanadas de carne congeladas', 10.00, 40, 6, TRUE, 'Precio por 3 unidades.'),

('Galletas Casino (paquete familiar)', 3.80, 70, 7, TRUE, NULL),
('Papas Lay’s clásicas', 2.50, 100, 7, TRUE, 'Por bolsa.'),
('Chifles artesanales', 4.00, 60, 7, TRUE, 'Por bolsa.'),

('Arroz Costeño superior 5 kg', 21.00, 50, 8, TRUE, NULL),
('Azúcar rubia 1 kg', 4.20, 80, 8, TRUE, NULL),
('Aceite Primor vegetal 1 L', 8.90, 60, 8, TRUE, NULL),

('Detergente Bolívar 1 kg', 6.50, 40, 9, TRUE, NULL),
('Papel higiénico Suave Gold (pack x4)', 7.80, 55, 9, TRUE, NULL),
('Lejía Clorox 1 L', 3.00, 70, 9, TRUE, NULL),

('Alcohol en gel 250 ml', 6.00, 90, 10, TRUE, NULL),
('Paracetamol genérico x 10 tabletas', 2.00, 110, 10, TRUE, NULL),
('Mascarillas KN95 (x1)', 1.50, 150, 10, TRUE, NULL),

('Pañales Huggies talla M (pack x20)', 27.00, 30, 11, TRUE, NULL),
('Leche maternizada NAN 1 (400 g)', 45.00, 25, 11, TRUE, NULL),
('Toallitas húmedas Babysec (pack x50)', 7.50, 50, 11, TRUE, NULL);

SELECT p.name, p.price, c.name as category FROM products p JOIN categories c ON p.category_id = c.id;

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL, -- Quién hizo el pedido (enlace a la tabla users)
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha y hora del pedido
    total_amount DECIMAL(10, 2) NOT NULL, -- Monto total del pedido
    status VARCHAR(50) DEFAULT 'Pending', -- Estado del pedido (ej: Pending, Processing, Shipped, Delivered, Cancelled)
    -- Aquí podrías añadir columnas para dirección de envío, método de pago, etc.
    -- shipping_address TEXT,
    -- payment_method VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Si el usuario se elimina, sus pedidos también (considera ON DELETE SET NULL si prefieres)
);

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL, -- A qué pedido pertenece este item (enlace a la tabla orders)
    product_id INT NOT NULL, -- Qué producto es (enlace a la tabla products)
    quantity INT NOT NULL, -- Cantidad comprada de este producto
    price_at_purchase DECIMAL(10, 2) NOT NULL, -- Precio del producto al momento de la compra (importante si los precios cambian)
    -- Aquí podrías añadir columnas para variaciones del producto si las tuvieras (ej: size, color)
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE, -- Si el pedido se elimina, sus items también
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT -- No permitir eliminar un producto si hay items de pedido asociados (o SET NULL si prefieres)
);