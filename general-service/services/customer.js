const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const asyncHandler = require("express-async-handler");
const User = require("../models/User");

const userController = {
  Register: asyncHandler(async (req, res) => {
    const { fullName, phone, email, password } = req.body;

    if (!fullName || !phone || !email || !password) {
      return res.status(400).json({ message: "Thiếu thông tin" });
    }

    const userExists = await User.findByEmail(email);
    if (userExists)
      return res
        .status(409)
        .json({ message: "Tài khoản tương ứng với email đã tồn tại." });

    const hashedPassword = await bcrypt.hash(password, 10);

    await User.createUser({
      fullName,
      phone,
      email,
      password: hashedPassword,
    });

    res.json({ message: "Đăng kí tài khoản khách hàng thành công!" });
  }),

  Login: asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    const user = await User.findByEmail(email);
    if (!user)
      return res
        .status(404)
        .json({ message: "Không tìm thấy tài khoản tương ứng với email." });

    const isMatch = await bcrypt.compare(password, user.UserPassword);
    if (!isMatch)
      return res.status(401).json({ message: "Email hoặc mật khẩu sai." });

    const token = jwt.sign(
      { id: user.UserID, email: user.UserEmail },
      process.env.JWT_SECRET,
      { expiresIn: "1h" }
    );

    res.json({
      message: "Đăng nhập thành công",
      token,
      user,
    });
  }),

  ResetPassword: asyncHandler(async (req, res) => {
    const { email, newPassword } = req.body;

    if (!email || !newPassword) {
      return res
        .status(400)
        .json({ message: "Thiếu thông tin email hoặc mật khẩu mới." });
    }

    const user = await User.findByEmail(email);
    if (!user) {
      return res
        .status(404)
        .json({ message: "Không tìm thấy tài khoản tương ứng với email." });
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await User.updatePassword(email, hashedPassword);

    res.json({ message: "Mật khẩu đã được cập nhật" });
  }),
};

module.exports = userController;
