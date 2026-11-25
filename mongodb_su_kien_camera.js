// ============================================================================
// HỆ THỐNG QUẢN LÝ PHẠT NGUỘI GIAO THÔNG - MONGODB SHELL SCRIPT (v2)
// Bổ sung JSON Schema Validation ($jsonSchema) và Unique Index
// Sinh viên: Võ Phạm Anh Đức - MSSV: 2574601080062 - Lớp: 71K31KHDL01
// ============================================================================

use QuanLyPhatNguoi_Evidence;
db.su_kien_camera.drop();

// 1. Tạo collection kèm ràng buộc JSON Schema Validation
db.createCollection("su_kien_camera", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["ma_su_kien", "bien_so_xe", "ma_camera", "thoi_gian_ghi_nhan", "trang_thai_kiem_duyet", "danh_sach_anh"],
      properties: {
        ma_su_kien: { bsonType: "string", description: "Mã sự kiện camera duy nhất" },
        ma_bien_ban: { bsonType: ["string", "null"], description: "Khóa tham chiếu sang BienBan (MySQL)" },
        bien_so_xe: { bsonType: "string", description: "Biển kiểm soát phương tiện" },
        ma_camera: { bsonType: "string", description: "Mã camera ghi nhận" },
        thoi_gian_ghi_nhan: { bsonType: "date" },
        trang_thai_kiem_duyet: {
          enum: ["Chờ thẩm định", "Đã lập biên bản", "Không đủ căn cứ"],
          description: "Trạng thái kiểm duyệt sự kiện"
        },
        nhan_dien_ai: {
          bsonType: "object",
          properties: {
            do_tin_cay_ocr: { bsonType: "double", minimum: 0, maximum: 1 }
          }
        },
        danh_sach_anh: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["loai_anh", "url_anh"],
            properties: {
              loai_anh: { bsonType: "string" },
              url_anh: { bsonType: "string" }
            }
          }
        }
      }
    }
  }
});

// 2. Tạo chỉ mục (Index) tăng tốc truy vấn và đồng bộ tham chiếu
db.su_kien_camera.createIndex({ ma_su_kien: 1 }, { unique: true });
db.su_kien_camera.createIndex({ ma_bien_ban: 1 });
db.su_kien_camera.createIndex({ bien_so_xe: 1, thoi_gian_ghi_nhan: -1 });

// 3. Nhập dữ liệu mẫu (insertMany)
db.su_kien_camera.insertMany([
  {
    ma_su_kien: "SK2026_1010_001",
    ma_bien_ban: "BB2026_0001",
    bien_so_xe: "51G-123.45",
    ma_camera: "CAM_Q1_01",
    thoi_gian_ghi_nhan: ISODate("2026-10-10T08:15:22Z"),
    trang_thai_kiem_duyet: "Đã lập biên bản",
    nhan_dien_ai: {
      bien_so_ocr: "51G12345",
      do_tin_cay_ocr: 0.984,
      loai_xe_ai: "Ô tô con",
      bounding_box: { x1: 412, y1: 289, x2: 588, y2: 345 }
    },
    cam_bien_moi_truong: { toc_do_kmh: 48, gioi_han_kmh: 50, trang_thai_den: "Đỏ", thoi_tiet: "Nắng nhẹ" },
    danh_sach_anh: [
      { loai_anh: "toan_canh", url_anh: "https://evidence.traffic.vn/2026/10/10/SK2026_1010_001_full.jpg", thoi_diem_chup: ISODate("2026-10-10T08:15:21Z"), mo_ta: "Ảnh toàn cảnh nút giao" },
      { loai_anh: "bien_so", url_anh: "https://evidence.traffic.vn/2026/10/10/SK2026_1010_001_plate.jpg", thoi_diem_chup: ISODate("2026-10-10T08:15:22Z"), mo_ta: "Ảnh cận cảnh biển số 51G-123.45" }
    ]
  },
  {
    ma_su_kien: "SK2026_1012_002",
    ma_bien_ban: "BB2026_0002",
    bien_so_xe: "51H-678.90",
    ma_camera: "CAM_BT_02",
    thoi_gian_ghi_nhan: ISODate("2026-10-12T17:40:05Z"),
    trang_thai_kiem_duyet: "Đã lập biên bản",
    nhan_dien_ai: {
      bien_so_ocr: "51H67890",
      do_tin_cay_ocr: 0.962,
      loai_xe_ai: "Ô tô con",
      bounding_box: { x1: 310, y1: 405, x2: 495, y2: 458 }
    },
    cam_bien_moi_truong: { toc_do_kmh: 76, gioi_han_kmh: 60, trang_thai_den: "Xanh", thoi_tiet: "Mưa phùn" },
    danh_sach_anh: [
      { loai_anh: "toc_do", url_anh: "https://evidence.traffic.vn/2026/10/12/SK2026_1012_002_radar.jpg", thoi_diem_chup: ISODate("2026-10-12T17:40:05Z"), mo_ta: "Khung hình ghi nhận tốc độ 76/60 km/h" }
    ]
  },
  {
    ma_su_kien: "SK2026_1015_003",
    ma_bien_ban: "BB2026_0003",
    bien_so_xe: "59P1-456.78",
    ma_camera: "CAM_TD_03",
    thoi_gian_ghi_nhan: ISODate("2026-10-15T14:20:10Z"),
    trang_thai_kiem_duyet: "Đã lập biên bản",
    nhan_dien_ai: {
      bien_so_ocr: "59P145678",
      do_tin_cay_ocr: 0.941,
      loai_xe_ai: "Xe mô tô",
      bounding_box: { x1: 250, y1: 320, x2: 370, y2: 365 }
    },
    cam_bien_moi_truong: { toc_do_kmh: 0, gioi_han_kmh: 50, trang_thai_den: "Xanh", thoi_tiet: "Nắng" },
    danh_sach_anh: [
      { loai_anh: "toan_canh", url_anh: "https://evidence.traffic.vn/2026/10/15/SK2026_1015_003_full.jpg", thoi_diem_chup: ISODate("2026-10-15T14:20:10Z"), mo_ta: "Đỗ xe dưới lòng đường trước cổng trung tâm thương mại" }
    ]
  },
  {
    ma_su_kien: "SK2026_1020_004",
    ma_bien_ban: "BB2026_0005",
    bien_so_xe: "51G-123.45",
    ma_camera: "CAM_BT_02",
    thoi_gian_ghi_nhan: ISODate("2026-10-20T09:10:00Z"),
    trang_thai_kiem_duyet: "Đã lập biên bản",
    nhan_dien_ai: {
      bien_so_ocr: "51G12345",
      do_tin_cay_ocr: 0.978,
      loai_xe_ai: "Ô tô con",
      bounding_box: { x1: 390, y1: 270, x2: 560, y2: 325 }
    },
    cam_bien_moi_truong: { toc_do_kmh: 78, gioi_han_kmh: 60, trang_thai_den: "Xanh", thoi_tiet: "Nắng" },
    danh_sach_anh: [
      { loai_anh: "toc_do", url_anh: "https://evidence.traffic.vn/2026/10/20/SK2026_1020_004_radar.jpg", thoi_diem_chup: ISODate("2026-10-20T09:10:00Z"), mo_ta: "Tốc độ đo được 78/60 km/h" }
    ]
  },
  {
    ma_su_kien: "SK2026_1021_005",
    ma_bien_ban: null,
    bien_so_xe: "51K-345.67",
    ma_camera: "CAM_TD_03",
    thoi_gian_ghi_nhan: ISODate("2026-10-21T10:05:18Z"),
    trang_thai_kiem_duyet: "Chờ thẩm định",
    nhan_dien_ai: {
      bien_so_ocr: "51K34567",
      do_tin_cay_ocr: 0.875,
      loai_xe_ai: "Ô tô con",
      bounding_box: { x1: 500, y1: 210, x2: 640, y2: 260 }
    },
    cam_bien_moi_truong: { toc_do_kmh: 68, gioi_han_kmh: 60, trang_thai_den: "Xanh", thoi_tiet: "Nắng" },
    danh_sach_anh: [
      { loai_anh: "toan_canh", url_anh: "https://evidence.traffic.vn/2026/10/21/SK2026_1021_005_full.jpg", thoi_diem_chup: ISODate("2026-10-21T10:05:18Z"), mo_ta: "Sự kiện chờ cán bộ xác nhận" }
    ]
  }
]);

// 4. Các truy vấn nghiệp vụ trên MongoDB
// Truy vấn A: Tìm sự kiện của xe 51G-123.45 có độ tin cậy OCR >= 0.90
printjson(db.su_kien_camera.find(
  { bien_so_xe: "51G-123.45", "nhan_dien_ai.do_tin_cay_ocr": { $gte: 0.90 } },
  { ma_su_kien: 1, ma_bien_ban: 1, "nhan_dien_ai.bien_so_ocr": 1, "nhan_dien_ai.do_tin_cay_ocr": 1, danh_sach_anh: 1 }
).toArray());

// Truy vấn B: Lọc các sự kiện có tốc độ thực tế vượt quá giới hạn tốc độ
printjson(db.su_kien_camera.find({
  $expr: { $gt: ["$cam_bien_moi_truong.toc_do_kmh", "$cam_bien_moi_truong.gioi_han_kmh"] }
}).toArray());

// Truy vấn C: Bổ sung ảnh bằng chứng mới vào mảng danh_sach_anh ($push)
db.su_kien_camera.updateOne(
  { ma_su_kien: "SK2026_1012_002" },
  {
    $push: {
      danh_sach_anh: {
        loai_anh: "bien_so",
        url_anh: "https://evidence.traffic.vn/2026/10/12/SK2026_1012_002_plate.jpg",
        thoi_diem_chup: ISODate("2026-10-12T17:40:06Z"),
        mo_ta: "Ảnh bổ sung biển số 51H-678.90"
      }
    }
  }
);

// Truy vấn D: Thống kê tổng số sự kiện, độ tin cậy OCR trung bình và tổng số ảnh theo từng Camera
printjson(db.su_kien_camera.aggregate([
  {
    $group: {
      _id: "$ma_camera",
      tong_su_kien: { $sum: 1 },
      avg_do_tin_cay_ocr: { $avg: "$nhan_dien_ai.do_tin_cay_ocr" },
      tong_so_anh: { $sum: { $size: "$danh_sach_anh" } }
    }
  },
  { $sort: { tong_su_kien: -1 } }
]).toArray());
