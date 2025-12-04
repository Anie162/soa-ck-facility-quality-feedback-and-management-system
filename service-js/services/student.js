const asyncHandler = require("express-async-handler");
const Student = require("../models/Student");

const studentController = {
  // Lấy thông tin sinh viên theo ID
  GetStudentById: asyncHandler(async (req, res) => {
    const { studentId } = req.params;

    if (!studentId) {
      return res
        .status(400)
        .json({ message: "Thiếu mã sinh viên (studentId)." });
    }

    const student = await Student.findById(studentId);
    if (!student) {
      return res
        .status(404)
        .json({ message: "Không thể tìm thấy sinh viên tương ứng." });
    }

    res.json({ message: "Tìm thấy sinh viên tương ứng.", student });
  }),

  // Xóa TuitionCode của sinh viên
  ClearTuitionCode: asyncHandler(async (req, res) => {
    const { studentId } = req.body;

    if (!studentId) {
      return res
        .status(400)
        .json({ message: "Thiếu mã sinh viên (studentId)." });
    }

    const student = await Student.findById(studentId);
    if (!student) {
      return res
        .status(404)
        .json({ message: "Không thể tìm thấy sinh viên tương ứng." });
    }

    await Student.clearTuitionCode(studentId);
    res.json({
      message: `Học phí của học kì này của sinh viên ${student.fullName} đã được thanh toán`,
    });
  }),

  // Thêm hoặc cập nhật TuitionCode
  SetTuitionCode: asyncHandler(async (req, res) => {
    const { studentId, tuitionCode } = req.body;

    if (!studentId || !tuitionCode) {
      return res
        .status(400)
        .json({ message: "Thiếu mã số sinh viên hoặc mã học phí." });
    }

    const student = await Student.findById(studentId);
    if (!student) {
      return res
        .status(404)
        .json({ message: "Không thể tìm thấy sinh viên tương ứng." });
    }

    await Student.setTuitionCode(studentId, tuitionCode);
    res.json({ message: "Mẫ học phí đã được cập nhật thành công" });
  }),
};

module.exports = studentController;
