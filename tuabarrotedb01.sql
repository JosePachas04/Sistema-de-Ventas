-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: tuabarrotedb
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Frutas y verduras',NULL,'2025-05-09 16:02:57'),(2,'Carnes y mariscos',NULL,'2025-05-09 16:02:57'),(3,'Desayuno y lácteos',NULL,'2025-05-09 16:02:57'),(4,'Panadería',NULL,'2025-05-09 16:02:57'),(5,'Bebidas',NULL,'2025-05-09 16:02:57'),(6,'Alimentos congelados',NULL,'2025-05-09 16:02:57'),(7,'Galletas y snacks',NULL,'2025-05-09 16:02:57'),(8,'Comestibles y productos básicos',NULL,'2025-05-09 16:02:57'),(9,'Necesidades del hogar',NULL,'2025-05-09 16:02:57'),(10,'Cuidado de la salud',NULL,'2025-05-09 16:02:57'),(11,'Bebé y embarazo',NULL,'2025-05-09 16:02:57');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `price_at_purchase` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `order_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `total_amount` decimal(10,2) NOT NULL,
  `status` varchar(50) DEFAULT 'Pending',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `price` decimal(10,2) NOT NULL,
  `stock` int NOT NULL DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `image_filename` varchar(255) DEFAULT NULL,
  `category_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_product_category` (`category_id`),
  CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'Plátano de Isla','Precio por kg.',3.50,50,1,'2025-05-09 16:12:36',NULL,1),(2,'Papa Canchán','Precio por kg.',2.00,100,1,'2025-05-09 16:12:36',NULL,1),(3,'Tomate Italiano','Precio por kg.',2.80,80,1,'2025-05-09 16:12:36',NULL,1),(4,'Pollo entero','Precio por kg.',9.50,30,1,'2025-05-09 16:12:36',NULL,2),(5,'Filete de pescado (merluza)','Precio por kg.',14.00,20,1,'2025-05-09 16:12:36',NULL,2),(6,'Carne molida de res','Precio por kg.',16.00,25,1,'2025-05-09 16:12:36',NULL,2),(7,'Leche Gloria evaporada 400 g',NULL,4.00,60,1,'2025-05-09 16:12:36',NULL,3),(8,'Pan de molde Bimbo 500 g',NULL,7.00,40,1,'2025-05-09 16:12:36',NULL,3),(9,'Queso fresco artesanal','Precio por kg.',12.00,15,1,'2025-05-09 16:12:36',NULL,3),(10,'Pan francés','Precio por unidad.',0.30,200,1,'2025-05-09 16:12:36',NULL,4),(11,'Pan integral artesanal','Precio por unidad.',1.20,50,1,'2025-05-09 16:12:36',NULL,4),(12,'Rosquitas andinas','Por bolsa.',4.50,35,1,'2025-05-09 16:12:36',NULL,4),(13,'Inca Kola 1.5 L',NULL,5.00,80,1,'2025-05-09 16:12:36',NULL,5),(14,'Refresco Cifrut 500 ml',NULL,2.00,120,1,'2025-05-09 16:12:36',NULL,5),(15,'Agua San Luis 2.5 L',NULL,3.80,90,1,'2025-05-09 16:12:36',NULL,5),(16,'Papas fritas precocidas 1 kg',NULL,9.00,25,1,'2025-05-09 16:12:36',NULL,6),(17,'Nuggets de pollo','Precio por 500 g.',12.00,30,1,'2025-05-09 16:12:36',NULL,6),(18,'Empanadas de carne congeladas','Precio por 3 unidades.',10.00,40,1,'2025-05-09 16:12:36',NULL,6),(19,'Galletas Casino (paquete familiar)',NULL,3.80,70,1,'2025-05-09 16:12:36',NULL,7),(20,'Papas Lay’s clásicas','Por bolsa.',2.50,100,1,'2025-05-09 16:12:36',NULL,7),(21,'Chifles Norteños Milys 250g','Contiene 250 gramos\r\nPlátano verde frito en hojuelas con maíz frito',9.90,60,1,'2025-05-09 16:12:36','Chifles_Nortenos_Milys_250g.jpg',7),(22,'Arroz Extra Costeño 750g','- Contiene 750 gramos\r\n- Arroz extra',4.90,50,1,'2025-05-09 16:12:36','Arroz_Extra_Costeno_750g.jpg',8),(23,'Azúcar Rubia Máxima 1kg','',4.20,80,1,'2025-05-09 16:12:36','Azucar_Rubia_Maxima_1kg.jpg',8),(24,'Aceite Vegetal Primor Premium Botella 900ml','- Contiene 900ml\r\n- Aceite vegetal\r\n- 100% vegetal\r\n- Con menos grasas saturadas',10.50,60,1,'2025-05-09 16:12:36','Aceite_Vegetal_Primor_Premium_Botella_900ml.jpg',8),(25,'Detergente en Polvo Bolívar Cuidado Total Floral 730g','- Contiene 730 gramos\r\n- Protege el color y las fibras de tus prendas\r\n- Con partículas protectoras de color\r\n- Cuida de tus manos y tu ropa',10.50,40,1,'2025-05-09 16:12:36','Detergente_en_Polvo_Bolivar_Cuidado_Total_Floral_730g.jpg',9),(26,'Papel Higiénico Suave Rindemax 4un','- Cantidad: 4 unidades\r\n- Papel higiénico doble hoja\r\n- Rendimiento y resistencia con más papel',7.90,55,1,'2025-05-09 16:12:36','Papel_Higienico_Suave_Rindemax_4un.jpg',9),(27,'Lejía Clorox Tradicional 4kg','- Contiene 4 kilos\r\n- Limpieza + Desinfección + Blanqueamiento\r\n- Elimina el virus causante del COVID-21\r\n- Limpia múltiples superficies',10.70,70,1,'2025-05-09 16:12:36','Lejia_Clorox_Tradicional_4kg.jpg',9),(28,'Alcohol en Gel Dermex Antibacterial Neutro','- Alcohol Gel\r\n- 65% alcohol y vitamina E\r\n- Elimina el 999% de gérmenes',7.50,90,1,'2025-05-09 16:12:36','Alcohol_en_Gel_Dermex_Antibacterial_Neutro.jpg',10),(29,'Paracetamol 1g Tableta','- CAJA 100 UN',33.00,110,1,'2025-05-09 16:12:36','Paracetamol_1g_Tableta.jpg',10),(30,'Mascarilla KN95','- KN95.\r\n- Mascarilla protectora (No uso médico).',10.00,150,1,'2025-05-09 16:12:36','Mascarilla_KN95.jpg',10),(31,'Pañal para Bebé Huggies Natural Care Talla M 60un','- Cantidad: 60 unidades\r\n- Talla: M\r\n- Tecnología Xtra-care\r\n- Ajuste elasticado\r\n- Con materiales extra suaves\r\n- Contiene fibras naturales\r\n- Ideal para bebés de 5.5 kilos a 9.5 kilos',53.90,30,1,'2025-05-09 16:12:36','Panal_para_Bebe_Huggies_Natural_Care_Talla_M_60un.jpg',11),(32,'Fórmula en Polvo de Inicio NAN Optipro 1 Lata 900g','',172.00,25,1,'2025-05-09 16:12:36','Leche_maternizada_NAN_1.jpg',11),(33,'Toallitas húmedas Babysec (pack x50)','',7.50,50,1,'2025-05-09 16:12:36','567707-800-auto.jpeg',11),(34,'Helado de Crema Peziduri Tricolor 900ml','Contiene 900 ml\r\nHelado cremoso\r\nSabor: Lúcuma / Fresa / Sabor vainilla',9.90,50,1,'2025-05-10 20:58:07','Helado_de_Crema_Peziduri_Tricolor_900ml.jpg',6),(35,'Agua Sin Gas Cielo Caja 20 L','Contenido: 20 Litros\r\nConservar en lugar fresco y seco\r\nPresentación: Caja',23.90,15,1,'2025-05-10 21:42:51','Agua_Sin_Gas_Cielo_Caja_20_L.jpg',5);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `role` varchar(50) NOT NULL DEFAULT 'customer',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$9kTRyGVS9v7fr7br$eca122803370911720e14a6c9dfc95a35cd6e702938fbac645d85c2754a265fb64ad3a49bce420a09a67e37810c85abcd90cfbfee199d18610ce7fb5acea0de8','2025-05-09 02:14:22','admin'),(2,'JosePachas','scrypt:32768:8:1$xaUSqyNA1n5K1F4S$24310cd407bd32ec0c7dcb65d3fea24b1a0910862641053491a6d22dad5893aff14d008636c1af1163ba94e92ee162667e7c96ebcd34991129e90a6358b0e50b','2025-05-09 02:32:46','customer'),(3,'AldairCastilla','scrypt:32768:8:1$By7KWZXfs3HSNWDH$8a95d3d1cecf5e32ee9a1619044e15582e8b1be120cbdfdd4aafd59611f6d026d097b205b397c81d0b7c2ab2f9ff3701b3b166ffc7d8dc99236de80eabdf8717','2025-05-10 20:48:47','customer');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-10 20:32:31
