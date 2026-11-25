-- ============================================================================
-- HỆ THỐNG QUẢN LÝ PHẠT NGUỘI GIAO THÔNG (CHUẨN HÓA 3NF - MYSQL)
-- Sinh viên: Võ Phạm Anh Đức - MSSV: 2574601080062 - Lớp: 71K31KHDL01
-- ============================================================================

-- 1. Khởi tạo cơ sở dữ liệu
DROP DATABASE IF EXISTS QuanLyPhatNguoi;
CREATE DATABASE QuanLyPhatNguoi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE QuanLyPhatNguoi;

-- 2. Tạo bảng ChuPhuongTien
CREATE TABLE ChuPhuongTien (
    ma_chu_xe VARCHAR(15) PRIMARY KEY,
    cccd_mst VARCHAR(20) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    so_dien_thoai VARCHAR(15) NOT NULL,
    dia_chi VARCHAR(255) NOT NULL
);

-- 3. Tạo bảng PhuongTien
CREATE TABLE PhuongTien (
    bien_so_xe VARCHAR(15) PRIMARY KEY,
    loai_xe VARCHAR(50) NOT NULL,
    nhan_hieu VARCHAR(50) NOT NULL,
    mau_son VARCHAR(30) NOT NULL,
    so_khung VARCHAR(30) NOT NULL UNIQUE,
    ma_chu_xe VARCHAR(15) NOT NULL,
    CONSTRAINT fk_pt_chuxe FOREIGN KEY (ma_chu_xe)
        REFERENCES ChuPhuongTien(ma_chu_xe)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 4. Tạo bảng Camera
CREATE TABLE Camera (
    ma_camera VARCHAR(15) PRIMARY KEY,
    ten_vi_tri VARCHAR(150) NOT NULL,
    quan_huyen VARCHAR(80) NOT NULL,
    toa_do_gps VARCHAR(50) NOT NULL,
    trang_thai VARCHAR(30) DEFAULT 'Hoạt động',
    CONSTRAINT chk_camera_tt CHECK (trang_thai IN ('Hoạt động', 'Bảo trì', 'Ngừng hoạt động'))
);

-- 5. Tạo bảng LoiViPham
CREATE TABLE LoiViPham (
    ma_loi VARCHAR(15) PRIMARY KEY,
    ten_loi VARCHAR(255) NOT NULL,
    muc_phat_min DECIMAL(12, 0) NOT NULL,
    muc_phat_max DECIMAL(12, 0) NOT NULL,
    hinh_phat_bo_sung VARCHAR(150) DEFAULT 'Không',
    CONSTRAINT chk_muc_phat CHECK (muc_phat_min > 0 AND muc_phat_max >= muc_phat_min)
);

-- 6. Tạo bảng BienBan
CREATE TABLE BienBan (
    ma_bien_ban VARCHAR(20) PRIMARY KEY,
    bien_so_xe VARCHAR(15) NOT NULL,
    ma_camera VARCHAR(15) NOT NULL,
    thoi_gian_vi_pham DATETIME NOT NULL,
    ngay_lap_bien_ban DATE NOT NULL,
    tong_tien_phat DECIMAL(12, 0) DEFAULT 0,
    trang_thai_xu_ly VARCHAR(40) DEFAULT 'Chờ xử lý',
    CONSTRAINT fk_bb_phuongtien FOREIGN KEY (bien_so_xe)
        REFERENCES PhuongTien(bien_so_xe)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bb_camera FOREIGN KEY (ma_camera)
        REFERENCES Camera(ma_camera)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_bb_trangthai CHECK (
        trang_thai_xu_ly IN ('Chờ xử lý', 'Đã gửi thông báo', 'Đã nộp phạt', 'Quá hạn')
    )
);

-- 7. Tạo bảng ChiTietBienBan
CREATE TABLE ChiTietBienBan (
    ma_bien_ban VARCHAR(20) NOT NULL,
    ma_loi VARCHAR(15) NOT NULL,
    muc_phat_ap_dung DECIMAL(12, 0) NOT NULL,
    ghi_chu VARCHAR(255),
    PRIMARY KEY (ma_bien_ban, ma_loi),
    CONSTRAINT fk_ctbb_bienban FOREIGN KEY (ma_bien_ban)
        REFERENCES BienBan(ma_bien_ban)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_ctbb_loi FOREIGN KEY (ma_loi)
        REFERENCES LoiViPham(ma_loi)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_muc_phat_ap_dung CHECK (muc_phat_ap_dung > 0)
);

-- ============================================================================
-- 8. NHẬP DỮ LIỆU MẪU
-- ============================================================================

INSERT INTO ChuPhuongTien VALUES
('CX001', '079090001234', 'Nguyễn Văn An', '0909123456', '120 Nguyễn Thị Minh Khai, Quận 3, TP.HCM'),
('CX002', '079085005678', 'Trần Thị Bích Ngọc', '0918234567', '45 Lê Lợi, Quận 1, TP.HCM'),
('CX003', '079092009012', 'Lê Hoàng Minh', '0987345678', '88 Phan Đăng Lưu, Quận Phú Nhuận, TP.HCM'),
('CX004', '031088003456', 'Công ty TNHH Vận tải Phương Nam', '02838123456', '210 Điện Biên Phủ, Quận Bình Thạnh, TP.HCM'),
('CX005', '079095007890', 'Phạm Quốc Bảo', '0933456789', '15 Võ Văn Ngân, TP. Thủ Đức, TP.HCM');

INSERT INTO PhuongTien VALUES
('51G-123.45', 'Ô tô con', 'Toyota Camry', 'Đen', 'RL4BE42K809123456', 'CX001'),
('51H-678.90', 'Ô tô con', 'Mazda CX-5', 'Trắng', 'RN2KE35M108678901', 'CX002'),
('59P1-456.78', 'Xe mô tô', 'Honda SH 150i', 'Xám', 'RLHJF8209MY456789', 'CX003'),
('51D-999.88', 'Xe tải', 'Hyundai Mighty', 'Xanh', 'KMFGA17PP9C999888', 'CX004'),
('51K-345.67', 'Ô tô con', 'VinFast VF8', 'Xanh rêu', 'RLLV1A2B3C4345678', 'CX001');

INSERT INTO Camera VALUES
('CAM_Q1_01', 'Ngã tư Nguyễn Huệ - Lê Lợi', 'Quận 1', '10.7745, 106.7012', 'Hoạt động'),
('CAM_BT_02', 'Nút giao Hàng Xanh', 'Quận Bình Thạnh', '10.8015, 106.7114', 'Hoạt động'),
('CAM_TD_03', 'Xa lộ Hà Nội - Ngã tư Thủ Đức', 'TP. Thủ Đức', '10.8492, 106.7718', 'Hoạt động'),
('CAM_Q3_04', 'Ngã tư Nam Kỳ Khởi Nghĩa - Võ Thị Sáu', 'Quận 3', '10.7856, 106.6889', 'Bảo trì');

INSERT INTO LoiViPham VALUES
('L01', 'Không chấp hành hiệu lệnh của đèn tín hiệu giao thông (Vượt đèn đỏ)', 4000000, 6000000, 'Tước GPLX 1-3 tháng'),
('L02', 'Điều khiển xe chạy quá tốc độ quy định từ 10 km/h đến 20 km/h', 4000000, 6000000, 'Không'),
('L03', 'Đi không đúng phần đường hoặc làn đường quy định', 4000000, 6000000, 'Tước GPLX 1-3 tháng'),
('L04', 'Dừng xe, đỗ xe tại nơi có biển Cấm dừng xe và đỗ xe', 800000, 1000000, 'Không'),
('L05', 'Người điều khiển xe mô tô không đội mũ bảo hiểm', 400000, 600000, 'Không');

INSERT INTO BienBan VALUES
('BB2026_0001', '51G-123.45', 'CAM_Q1_01', '2026-10-10 08:15:22', '2026-10-11', 5000000, 'Đã nộp phạt'),
('BB2026_0002', '51H-678.90', 'CAM_BT_02', '2026-10-12 17:40:05', '2026-10-13', 9500000, 'Đã gửi thông báo'),
('BB2026_0003', '59P1-456.78', 'CAM_TD_03', '2026-10-15 14:20:10', '2026-10-16', 1300000, 'Chờ xử lý'),
('BB2026_0004', '51D-999.88', 'CAM_TD_03', '2026-10-18 22:05:45', '2026-10-19', 5000000, 'Quá hạn'),
('BB2026_0005', '51G-123.45', 'CAM_BT_02', '2026-10-20 09:10:00', '2026-10-21', 5000000, 'Chờ xử lý');

INSERT INTO ChiTietBienBan VALUES
('BB2026_0001', 'L01', 5000000, 'Vượt đèn đỏ hướng Lê Lợi ra Đồng Khởi'),
('BB2026_0002', 'L02', 5000000, 'Tốc độ đo được 76/60 km/h'),
('BB2026_0002', 'L03', 4500000, 'Lấn sang làn xe máy'),
('BB2026_0003', 'L04', 800000, 'Đỗ xe dưới lòng đường trước cổng trung tâm thương mại'),
('BB2026_0003', 'L05', 500000, 'Không đội mũ bảo hiểm khi lưu thông'),
('BB2026_0004', 'L03', 5000000, 'Xe tải đi vào làn xe con giờ cao điểm'),
('BB2026_0005', 'L02', 5000000, 'Tốc độ đo được 78/60 km/h');

-- ============================================================================
-- 9. CÁC TRUY VẤN NGHIỆP VỤ
-- ============================================================================

-- Truy vấn 1: Danh sách biên bản chưa hoàn tất nộp phạt kèm thông tin chủ phương tiện
SELECT bb.ma_bien_ban, bb.thoi_gian_vi_pham, pt.bien_so_xe, pt.loai_xe,
       cpt.ho_ten AS chu_phuong_tien, cpt.so_dien_thoai, cpt.dia_chi,
       cam.ten_vi_tri AS dia_diem_vi_pham, bb.tong_tien_phat, bb.trang_thai_xu_ly
FROM BienBan bb
JOIN PhuongTien pt ON bb.bien_so_xe = pt.bien_so_xe
JOIN ChuPhuongTien cpt ON pt.ma_chu_xe = cpt.ma_chu_xe
JOIN Camera cam ON bb.ma_camera = cam.ma_camera
WHERE bb.trang_thai_xu_ly IN ('Chờ xử lý', 'Đã gửi thông báo', 'Quá hạn')
ORDER BY bb.thoi_gian_vi_pham DESC;

-- Truy vấn 2: Chi tiết các lỗi vi phạm thuộc biên bản BB2026_0002
SELECT ct.ma_bien_ban, lvp.ma_loi, lvp.ten_loi,
       ct.muc_phat_ap_dung, lvp.hinh_phat_bo_sung, ct.ghi_chu
FROM ChiTietBienBan ct
JOIN LoiViPham lvp ON ct.ma_loi = lvp.ma_loi
WHERE ct.ma_bien_ban = 'BB2026_0002';

-- Truy vấn 3: Thống kê số lượt vi phạm và tổng tiền phạt theo từng Camera
SELECT cam.ma_camera, cam.ten_vi_tri, cam.quan_huyen,
       COUNT(bb.ma_bien_ban) AS so_luot_vi_pham,
       COALESCE(SUM(bb.tong_tien_phat), 0) AS tong_tien_phat_ghi_nhan,
       SUM(CASE WHEN bb.trang_thai_xu_ly = 'Đã nộp phạt' THEN bb.tong_tien_phat ELSE 0 END) AS da_thu_ngan_sach
FROM Camera cam
LEFT JOIN BienBan bb ON cam.ma_camera = bb.ma_camera
GROUP BY cam.ma_camera, cam.ten_vi_tri, cam.quan_huyen
ORDER BY so_luot_vi_pham DESC;

-- Truy vấn 4: Thống kê các phương tiện tái phạm nhiều lần (>= 2 biên bản)
SELECT pt.bien_so_xe, pt.nhan_hieu, cpt.ho_ten AS chu_so_huu, cpt.so_dien_thoai,
       COUNT(bb.ma_bien_ban) AS so_lan_vi_pham,
       SUM(bb.tong_tien_phat) AS tong_tien_phat_tich_luy
FROM PhuongTien pt
JOIN ChuPhuongTien cpt ON pt.ma_chu_xe = cpt.ma_chu_xe
JOIN BienBan bb ON pt.bien_so_xe = bb.bien_so_xe
GROUP BY pt.bien_so_xe, pt.nhan_hieu, cpt.ho_ten, cpt.so_dien_thoai
HAVING COUNT(bb.ma_bien_ban) >= 2;

-- Truy vấn 5: Truy vấn lồng tìm các biên bản có mức phạt cao hơn trung bình hệ thống
SELECT ma_bien_ban, bien_so_xe, thoi_gian_vi_pham, tong_tien_phat, trang_thai_xu_ly
FROM BienBan
WHERE tong_tien_phat > (SELECT AVG(tong_tien_phat) FROM BienBan)
ORDER BY tong_tien_phat DESC;
