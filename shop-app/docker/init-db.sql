-- 가비아 쇼핑몰 데이터베이스 초기화 스크립트
-- PostgreSQL 15 기준

-- 기본 카테고리 데이터 삽입
INSERT INTO categories (name, description) VALUES
('Electronics', '전자제품 - 컴퓨터, 스마트폰, 태블릿 등'),
('Audio', '오디오 기기 - 헤드폰, 스피커, 이어폰 등'),
('Accessories', '액세서리 - 키보드, 마우스, 케이블 등'),
('Computing', '컴퓨팅 - 노트북, 데스크탑, 모니터 등'),
('Mobile', '모바일 - 스마트폰, 태블릿, 액세서리 등')
ON CONFLICT (name) DO NOTHING;

-- 샘플 제품 데이터 삽입
INSERT INTO products (name, price, description, category, stock, image_url, is_active) VALUES
-- Electronics
('Laptop Pro 15', 1299000, '15인치 고성능 프로페셔널 노트북. Intel Core i7, 16GB RAM, 512GB SSD', 'Electronics', 15, '/images/laptop-pro-15.jpg', true),
('Smartphone X Pro', 899000, '6.7인치 OLED, 5G 지원, 트리플 카메라', 'Mobile', 30, '/images/smartphone-x.jpg', true),
('4K Monitor 27"', 599000, '27인치 4K UHD IPS 패널, 144Hz, HDR10', 'Computing', 20, '/images/monitor-4k.jpg', true),
('Gaming Laptop', 1899000, '17인치 게이밍 노트북, RTX 4070, 32GB RAM', 'Computing', 8, '/images/gaming-laptop.jpg', true),
('Tablet Pro 12.9', 1199000, '12.9인치 태블릿, Apple M2 칩, 256GB', 'Mobile', 12, '/images/tablet-pro.jpg', true),

-- Audio
('Wireless Headphones Pro', 299000, '액티브 노이즈 캔슬링, 30시간 재생', 'Audio', 50, '/images/headphones.jpg', true),
('Bluetooth Speaker', 149000, '포터블 블루투스 스피커, 방수 기능', 'Audio', 45, '/images/speaker.jpg', true),
('Studio Monitor Speakers', 599000, '스튜디오급 모니터 스피커 (페어)', 'Audio', 15, '/images/studio-monitors.jpg', true),
('Wireless Earbuds Pro', 199000, 'ANC 지원, 무선 충전 케이스', 'Audio', 60, '/images/earbuds.jpg', true),
('USB Microphone', 179000, '스튜디오급 USB 마이크, 팝 필터 포함', 'Audio', 25, '/images/microphone.jpg', true),

-- Accessories
('Mechanical Keyboard RGB', 189000, 'RGB 기계식 키보드, Cherry MX 스위치', 'Accessories', 40, '/images/keyboard.jpg', true),
('Gaming Mouse Pro', 79000, '고정밀 게이밍 마우스, 16000 DPI', 'Accessories', 60, '/images/mouse.jpg', true),
('USB-C Hub 7-in-1', 59000, '7-in-1 USB-C 허브, 100W PD 충전', 'Accessories', 80, '/images/usb-hub.jpg', true),
('Webcam 4K', 129000, '4K 해상도 웹캠, 자동 초점', 'Accessories', 35, '/images/webcam.jpg', true),
('External SSD 1TB', 159000, '포터블 외장 SSD, 1050MB/s 속도', 'Accessories', 55, '/images/ssd.jpg', true),
('Monitor Arm', 89000, '모니터 암, 17-32인치 지원, VESA 마운트', 'Accessories', 30, '/images/monitor-arm.jpg', true),
('Laptop Stand', 49000, '알루미늄 노트북 스탠드, 각도 조절', 'Accessories', 70, '/images/laptop-stand.jpg', true),
('Cable Management Kit', 29000, '케이블 정리 키트, 15종 포함', 'Accessories', 100, '/images/cable-kit.jpg', true),
('Phone Case Premium', 39000, '프리미엄 가죽 케이스, 카드 슬롯', 'Mobile', 120, '/images/phone-case.jpg', true),
('Screen Protector', 19000, '강화 유리 보호필름, 2매 세트', 'Mobile', 150, '/images/screen-protector.jpg', true)
ON CONFLICT (id) DO NOTHING;

-- 샘플 주문 데이터 (테스트용)
INSERT INTO orders (user_id, total_amount, status, shipping_address, notes) VALUES
(1, 1498000, 'completed', '서울시 강남구 테헤란로 123', '빠른 배송 부탁드립니다'),
(2, 508000, 'processing', '서울시 서초구 서초대로 456', NULL),
(3, 188000, 'pending', '경기도 성남시 분당구 정자로 789', '문 앞에 놓아주세요'),
(1, 299000, 'completed', '서울시 강남구 테헤란로 123', NULL)
ON CONFLICT (id) DO NOTHING;

-- 주문 항목 데이터
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 1299000, 1299000),
(1, 13, 1, 199000, 199000),
(2, 6, 1, 299000, 299000),
(2, 10, 1, 179000, 179000),
(2, 15, 1, 159000, 159000),
(2, 12, 1, 79000, 79000),
(3, 11, 2, 189000, 378000),
(4, 6, 1, 299000, 299000)
ON CONFLICT (id) DO NOTHING;

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- 뷰 생성 (통계용)
CREATE OR REPLACE VIEW product_stats AS
SELECT 
    category,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    SUM(stock) as total_stock
FROM products
WHERE is_active = true
GROUP BY category;

CREATE OR REPLACE VIEW order_stats AS
SELECT 
    status,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM orders
GROUP BY status;

-- 확인 쿼리
SELECT 'Categories:', COUNT(*) FROM categories;
SELECT 'Products:', COUNT(*) FROM products;
SELECT 'Orders:', COUNT(*) FROM orders;
