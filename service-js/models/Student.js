const { pool, sql } = require("../configs/database");

class Student {
  constructor({ StudentID, StudentFullName, StudentEmail, StudentPhone, CurrentTuitionCode }) {
    this.id = StudentID;
    this.fullName = StudentFullName;
    this.email = StudentEmail;
    this.phone = StudentPhone;
    this.tuitionCode = CurrentTuitionCode ;
  }

  static fromRecord(record) {
    return new Student(record);
  }

  // Tìm Student theo ID
  static async findById(id) {
    const result = await pool.request()
      .input("StudentID", sql.Char(8), id)
      .query("SELECT * FROM Student WHERE StudentID = @StudentID");

    if (result.recordset.length === 0) return null;
    return Student.fromRecord(result.recordset[0]);
  }

  // Xoá TuitionCode (set NULL)
  static async clearTuitionCode(id) {
    await pool.request()
      .input("StudentID", sql.Char(8), id)
      .query("UPDATE Student SET CurrentTuitionCode = NULL WHERE StudentID = @StudentID");
  }

  // Thêm hoặc cập nhật TuitionCode
  static async setTuitionCode(id, tuitionCode) {
    // Cộng dồn học phí vào trong TuitionCode học kì hiện tại nếu sinh viên chưa thanh toán ở học kì trước
    await pool.request()
      .input("StudentID", sql.Char(8), id)
      .input("CurrentTuitionCode", sql.Char(17), tuitionCode)
      .query("UPDATE Student SET CurrentTuitionCode = @CurrentTuitionCode WHERE StudentID = @StudentID");
  }
}

module.exports = Student;