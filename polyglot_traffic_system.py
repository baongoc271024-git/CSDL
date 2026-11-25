"""
HỆ THỐNG QUẢN LÝ PHẠT NGUỘI GIAO THÔNG - TÍCH HỢP MYSQL & MONGODB (v2)
Bổ sung lọc theo ngưỡng OCR và đồng bộ tham chiếu khi xóa biên bản (Cross-DB Sync)
Sinh viên: Võ Phạm Anh Đức - MSSV: 2574601080062 - Lớp: 71K31KHDL01
Cài đặt thư viện: pip install mysql-connector-python pymongo
"""

from datetime import datetime, timezone
import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient


class PolyglotTrafficSystem:
    def __init__(self, mysql_config: dict, mongo_uri: str, mongo_db_name: str):
        self.mysql_config = mysql_config
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mysql_conn = None
        self.mongo_client = None
        self.mongo_db = None

    def connect(self):
        """Kết nối đồng thời đến cả MySQL và MongoDB."""
        self.mysql_conn = mysql.connector.connect(**self.mysql_config)
        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[self.mongo_db_name]
        self.mongo_client.admin.command("ping")
        print("[OK] Đã kết nối đồng thời tới MySQL và MongoDB.")

    def close(self):
        """Đóng kết nối cả hai hệ quản trị cơ sở dữ liệu."""
        if self.mysql_conn and self.mysql_conn.is_connected():
            self.mysql_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
        print("[OK] Đã đóng kết nối MySQL và MongoDB.")

    # =========================================================================
    # 1. THAO TÁC CRUD TRÊN MYSQL
    # =========================================================================
    def create_bien_ban_mysql(
        self,
        ma_bien_ban: str,
        bien_so_xe: str,
        ma_camera: str,
        thoi_gian_vp: str,
        ngay_lap: str,
        chi_tiet_loi: list,
        trang_thai: str = "Chờ xử lý",
    ):
        tong_tien = sum(item[1] for item in chi_tiet_loi)
        cursor = self.mysql_conn.cursor()
        try:
            sql_bb = """
                INSERT INTO BienBan (
                    ma_bien_ban, bien_so_xe, ma_camera, thoi_gian_vi_pham,
                    ngay_lap_bien_ban, tong_tien_phat, trang_thai_xu_ly
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql_bb,
                (
                    ma_bien_ban,
                    bien_so_xe,
                    ma_camera,
                    thoi_gian_vp,
                    ngay_lap,
                    tong_tien,
                    trang_thai,
                ),
            )

            sql_ct = """
                INSERT INTO ChiTietBienBan (ma_bien_ban, ma_loi, muc_phat_ap_dung, ghi_chu)
                VALUES (%s, %s, %s, %s)
            """
            for ma_loi, muc_phat, ghi_chu in chi_tiet_loi:
                cursor.execute(sql_ct, (ma_bien_ban, ma_loi, muc_phat, ghi_chu))

            self.mysql_conn.commit()
            print(f"[MySQL INSERT] Đã tạo biên bản {ma_bien_ban} (Tổng phạt: {tong_tien:,.0f} VNĐ).")
        except Error as e:
            self.mysql_conn.rollback()
            print(f"[MySQL INSERT LỖI - Rollback]: {e}")
        finally:
            cursor.close()

    def update_trang_thai_bien_ban_mysql(self, ma_bien_ban: str, trang_thai_moi: str):
        cursor = self.mysql_conn.cursor()
        try:
            sql = "UPDATE BienBan SET trang_thai_xu_ly = %s WHERE ma_bien_ban = %s"
            cursor.execute(sql, (trang_thai_moi, ma_bien_ban))
            self.mysql_conn.commit()
            print(f"[MySQL UPDATE] Biên bản {ma_bien_ban} -> '{trang_thai_moi}' ({cursor.rowcount} dòng).")
        except Error as e:
            self.mysql_conn.rollback()
            print(f"[MySQL UPDATE LỖI]: {e}")
        finally:
            cursor.close()

    def delete_bien_ban_dong_bo(self, ma_bien_ban: str):
        """
        Xóa biên bản trên MySQL đồng thời gỡ khóa tham chiếu ma_bien_ban trên MongoDB
        để tránh tình trạng tham chiếu treo (Dangling Reference).
        """
        cursor = self.mysql_conn.cursor()
        try:
            sql = "DELETE FROM BienBan WHERE ma_bien_ban = %s"
            cursor.execute(sql, (ma_bien_ban,))
            self.mysql_conn.commit()

            col = self.mongo_db["su_kien_camera"]
            res = col.update_many(
                {"ma_bien_ban": ma_bien_ban},
                {"$set": {"ma_bien_ban": None, "trang_thai_kiem_duyet": "Chờ thẩm định"}},
            )
            print(
                f"[SYNC DELETE] Đã xóa biên bản {ma_bien_ban} trên MySQL và "
                f"gỡ tham chiếu trên {res.modified_count} document MongoDB."
            )
        except Error as e:
            self.mysql_conn.rollback()
            print(f"[SYNC DELETE LỖI]: {e}")
        finally:
            cursor.close()

    # =========================================================================
    # 2. THAO TÁC CRUD & LỌC DỮ LIỆU TRÊN MONGODB
    # =========================================================================
    def create_su_kien_mongo(self, doc: dict):
        col = self.mongo_db["su_kien_camera"]
        res = col.insert_one(doc)
        print(f"[MongoDB INSERT] Đã lưu sự kiện {doc.get('ma_su_kien')} (_id={res.inserted_id}).")

    def read_su_kien_by_bien_so_mongo(self, bien_so_xe: str) -> list:
        col = self.mongo_db["su_kien_camera"]
        return list(col.find({"bien_so_xe": bien_so_xe}).sort("thoi_gian_ghi_nhan", -1))

    def filter_su_kien_theo_ocr_mongo(self, min_confidence: float = 0.90) -> list:
        """Truy vấn các sự kiện camera có độ tin cậy nhận diện OCR >= ngưỡng quy định."""
        col = self.mongo_db["su_kien_camera"]
        query = {"nhan_dien_ai.do_tin_cay_ocr": {"$gte": min_confidence}}
        projection = {"_id": 0, "ma_su_kien": 1, "bien_so_xe": 1, "nhan_dien_ai": 1, "trang_thai_kiem_duyet": 1}
        return list(col.find(query, projection))

    def link_su_kien_voi_bien_ban_mongo(self, ma_su_kien: str, ma_bien_ban: str):
        col = self.mongo_db["su_kien_camera"]
        res = col.update_one(
            {"ma_su_kien": ma_su_kien},
            {"$set": {"ma_bien_ban": ma_bien_ban, "trang_thai_kiem_duyet": "Đã lập biên bản"}},
        )
        print(f"[MongoDB UPDATE] Sự kiện {ma_su_kien} gắn biên bản {ma_bien_ban} (matched={res.matched_count}).")

    def delete_su_kien_mongo(self, ma_su_kien: str):
        col = self.mongo_db["su_kien_camera"]
        res = col.delete_one({"ma_su_kien": ma_su_kien})
        print(f"[MongoDB DELETE] Đã xóa sự kiện {ma_su_kien} (deleted={res.deleted_count}).")

    # =========================================================================
    # 3. NGHIỆP VỤ TÍCH HỢP DỮ LIỆU TỪ MYSQL VÀ MONGODB
    # =========================================================================
    def tra_cuu_ho_so_vi_pham_tong_hop(self, bien_so_xe: str) -> dict:
        cursor = self.mysql_conn.cursor(dictionary=True)
        try:
            # Bước 1: Truy vấn thông tin phương tiện & chủ sở hữu từ MySQL
            sql_pt = """
                SELECT pt.bien_so_xe, pt.loai_xe, pt.nhan_hieu, pt.mau_son, pt.so_khung,
                       cpt.ma_chu_xe, cpt.ho_ten, cpt.cccd_mst, cpt.so_dien_thoai, cpt.dia_chi
                FROM PhuongTien pt
                JOIN ChuPhuongTien cpt ON pt.ma_chu_xe = cpt.ma_chu_xe
                WHERE pt.bien_so_xe = %s
            """
            cursor.execute(sql_pt, (bien_so_xe,))
            phuong_tien = cursor.fetchone()
            if not phuong_tien:
                return {"error": f"Không tìm thấy phương tiện {bien_so_xe} trong MySQL."}

            # Bước 2: Truy vấn các biên bản & chi tiết lỗi từ MySQL
            sql_bb = """
                SELECT bb.ma_bien_ban, bb.thoi_gian_vi_pham, bb.ngay_lap_bien_ban,
                       bb.tong_tien_phat, bb.trang_thai_xu_ly, cam.ten_vi_tri,
                       lvp.ma_loi, lvp.ten_loi, ct.muc_phat_ap_dung, lvp.hinh_phat_bo_sung
                FROM BienBan bb
                JOIN Camera cam ON bb.ma_camera = cam.ma_camera
                LEFT JOIN ChiTietBienBan ct ON bb.ma_bien_ban = ct.ma_bien_ban
                LEFT JOIN LoiViPham lvp ON ct.ma_loi = lvp.ma_loi
                WHERE bb.bien_so_xe = %s
                ORDER BY bb.thoi_gian_vi_pham DESC
            """
            cursor.execute(sql_bb, (bien_so_xe,))
            rows_bb = cursor.fetchall()

            bien_ban_map = {}
            for r in rows_bb:
                mbb = r["ma_bien_ban"]
                if mbb not in bien_ban_map:
                    bien_ban_map[mbb] = {
                        "ma_bien_ban": mbb,
                        "thoi_gian_vi_pham": str(r["thoi_gian_vi_pham"]),
                        "ngay_lap_bien_ban": str(r["ngay_lap_bien_ban"]),
                        "tong_tien_phat": float(r["tong_tien_phat"]),
                        "trang_thai_xu_ly": r["trang_thai_xu_ly"],
                        "dia_diem": r["ten_vi_tri"],
                        "cac_loi": [],
                        "bang_chung_camera": [],
                    }
                if r["ma_loi"]:
                    bien_ban_map[mbb]["cac_loi"].append(
                        {
                            "ma_loi": r["ma_loi"],
                            "ten_loi": r["ten_loi"],
                            "muc_phat_ap_dung": float(r["muc_phat_ap_dung"]),
                            "hinh_phat_bo_sung": r["hinh_phat_bo_sung"],
                        }
                    )

            # Bước 3: Truy vấn log nhận diện AI & ảnh bằng chứng từ MongoDB
            su_kien_docs = self.read_su_kien_by_bien_so_mongo(bien_so_xe)
            su_kien_chua_lap_bb = []
            for doc in su_kien_docs:
                evidence_summary = {
                    "ma_su_kien": doc.get("ma_su_kien"),
                    "ma_camera": doc.get("ma_camera"),
                    "thoi_gian_ghi_nhan": str(doc.get("thoi_gian_ghi_nhan")),
                    "trang_thai_kiem_duyet": doc.get("trang_thai_kiem_duyet"),
                    "bien_so_ocr": doc.get("nhan_dien_ai", {}).get("bien_so_ocr"),
                    "do_tin_cay_ocr": doc.get("nhan_dien_ai", {}).get("do_tin_cay_ocr"),
                    "toc_do_kmh": doc.get("cam_bien_moi_truong", {}).get("toc_do_kmh"),
                    "so_anh_bang_chung": len(doc.get("danh_sach_anh", [])),
                    "url_anh": [a.get("url_anh") for a in doc.get("danh_sach_anh", [])],
                }
                mbb_ref = doc.get("ma_bien_ban")
                if mbb_ref and mbb_ref in bien_ban_map:
                    bien_ban_map[mbb_ref]["bang_chung_camera"].append(evidence_summary)
                else:
                    su_kien_chua_lap_bb.append(evidence_summary)

            return {
                "phuong_tien_va_chu_xe": phuong_tien,
                "danh_sach_bien_ban": list(bien_ban_map.values()),
                "su_kien_camera_chua_lap_bien_ban": su_kien_chua_lap_bb,
            }
        finally:
            cursor.close()


if __name__ == "__main__":
    MYSQL_CFG = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_mysql_password",  # Cập nhật mật khẩu MySQL trên máy của bạn
        "database": "QuanLyPhatNguoi",
    }
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "QuanLyPhatNguoi_Evidence"

    system = PolyglotTrafficSystem(MYSQL_CFG, MONGO_URI, MONGO_DB)
    system.connect()

    try:
        print("\n=== 1. TRA CỨU HỒ SƠ TÍCH HỢP (MYSQL + MONGODB) CHO XE 51G-123.45 ===")
        ho_so = system.tra_cuu_ho_so_vi_pham_tong_hop("51G-123.45")
        pt_info = ho_so["phuong_tien_va_chu_xe"]
        print(f"Chủ xe: {pt_info['ho_ten']} | SĐT: {pt_info['so_dien_thoai']} | Xe: {pt_info['bien_so_xe']} ({pt_info['nhan_hieu']})")
        for bb in ho_so["danh_sach_bien_ban"]:
            print(f"  + Biên bản {bb['ma_bien_ban']} ({bb['trang_thai_xu_ly']}) - Tổng phạt: {bb['tong_tien_phat']:,.0f} VNĐ")
            for loi in bb["cac_loi"]:
                print(f"      * Lỗi {loi['ma_loi']}: {loi['ten_loi']} -> {loi['muc_phat_ap_dung']:,.0f} VNĐ")
            for ev in bb["bang_chung_camera"]:
                print(f"      * Bằng chứng MongoDB [{ev['ma_su_kien']}]: OCR={ev['bien_so_ocr']} ({ev['do_tin_cay_ocr']}), {ev['so_anh_bang_chung']} ảnh")

        print("\n=== 2. LỌC SỰ KIỆN CÓ ĐỘ TIN CẬY OCR >= 0.95 TRÊN MONGODB ===")
        high_conf = system.filter_su_kien_theo_ocr_mongo(0.95)
        for item in high_conf:
            print(f"  - {item['ma_su_kien']} | Xe: {item['bien_so_xe']} | OCR: {item['nhan_dien_ai']['do_tin_cay_ocr']}")

        print("\n=== 3. KIỂM THỬ THÊM, CẬP NHẬT & ĐỒNG BỘ XÓA TRÊN HAI HỆ QUẢN TRỊ ===")
        new_event = {
            "ma_su_kien": "SK2026_1120_TEST",
            "ma_bien_ban": None,
            "bien_so_xe": "51K-345.67",
            "ma_camera": "CAM_TD_03",
            "thoi_gian_ghi_nhan": datetime(2026, 11, 20, 14, 0, 0, tzinfo=timezone.utc),
            "trang_thai_kiem_duyet": "Chờ thẩm định",
            "nhan_dien_ai": {"bien_so_ocr": "51K34567", "do_tin_cay_ocr": 0.95, "loai_xe_ai": "Ô tô con"},
            "cam_bien_moi_truong": {"toc_do_kmh": 72, "gioi_han_kmh": 60, "trang_thai_den": "Xanh", "thoi_tiet": "Nắng"},
            "danh_sach_anh": [{"loai_anh": "toc_do", "url_anh": "https://evidence.traffic.vn/test.jpg"}],
        }
        system.create_su_kien_mongo(new_event)
        system.create_bien_ban_mysql(
            ma_bien_ban="BB2026_9999",
            bien_so_xe="51K-345.67",
            ma_camera="CAM_TD_03",
            thoi_gian_vp="2026-11-20 14:00:00",
            ngay_lap="2026-11-20",
            chi_tiet_loi=[("L02", 4500000, "Chạy quá tốc độ 72/60 km/h")],
        )
        system.link_su_kien_voi_bien_ban_mongo("SK2026_1120_TEST", "BB2026_9999")
        system.update_trang_thai_bien_ban_mysql("BB2026_9999", "Đã nộp phạt")

        # Kiểm thử xóa đồng bộ (gỡ ma_bien_ban trên MongoDB trước khi xóa sự kiện thử nghiệm)
        system.delete_bien_ban_dong_bo("BB2026_9999")
        system.delete_su_kien_mongo("SK2026_1120_TEST")
    finally:
        system.close()
