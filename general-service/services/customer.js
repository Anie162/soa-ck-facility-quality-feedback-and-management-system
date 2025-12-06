const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const asyncHandler = require("express-async-handler");
const Customer = require("../models/Customer");

const customerController = {
  Register: asyncHandler(async (req, res) => {
    const { fullName, phone, email, password } = req.body;

    if (!fullName || !phone || !email || !password) {
      return res.status(400).json({ message: "Thiếu thông tin" });
    }

    const customerExists = await Customer.findByEmail(email);
    if (customerExists)
      return res
        .status(409)
        .json({ message: "Tài khoản tương ứng với email đã tồn tại." });

    const hashedPassword = await bcrypt.hash(password, 10);

    await Customer.createCustomer({
      fullName,
      phone,
      email,
      password: hashedPassword,
    });

    res.json({ message: "Đăng kí tài khoản khách hàng thành công!" });
  }),

  Login: asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    const customer = await Customer.findByEmail(email);
    if (!customer)
      return res
        .status(404)
        .json({ message: "Không tìm thấy tài khoản tương ứng với email." });

    const isMatch = await bcrypt.compare(password, customer.CustomerPassword);
    if (!isMatch)
      return res.status(401).json({ message: "Email hoặc mật khẩu sai." });

    const token = jwt.sign(
      { id: customer.CustomerID, email: customer.CustomerEmail },
      process.env.JWT_SECRET,
      { expiresIn: "1h" }
    );

    res.json({
      message: "Đăng nhập thành công",
      token,
      customer,
    });
  }),

  Withdraw: asyncHandler(async (req, res) => {
    const { customerId, amount } = req.body;

    if (!customerId || !amount || amount <= 0) {
      return res
        .status(400)
        .json({ message: "Thiếu thông tin hoặc số tiền không hợp lệ." });
    }

    const customer = await Customer.findById(customerId);
    if (!customer)
      return res
        .status(404)
        .json({ message: "Không tìm thấy khách hàng tương ứng." });

    if (customer.CustomerBalance < amount) {
      return res.status(400).json({ message: "Số dư không đủ" });
    }

    await Customer.withdraw(customerId, amount);
    res.json({ message: "Rút tiền thành công" });
  }),

  Deposit: asyncHandler(async (req, res) => {
    const { customerEmail, amount } = req.body;

    if (!customerEmail || !amount || amount <= 0) {
      return res
        .status(400)
        .json({ message: "Thiếu thông tin hoặc số tiền nạp không hợp lệ." });
    }

    const customer = await Customer.findByEmail(customerEmail);

    if (!customer) {
      return res
        .status(404)
        .json({ message: "Không tìm thấy khách hàng tương ứng với email." });
    }

    await Customer.deposit(customer.CustomerID, amount);
    res.json({ message: "Nạp tiền thành công" });
  }),

  DepositWithID: asyncHandler(async (req, res) => {
    const { customerID, amount } = req.body;

    if (!customerID || !amount || amount <= 0) {
      return res
        .status(400)
        .json({ message: "Thiếu thông tin hoặc số tiền nạp không hợp lệ." });
    }

    const customer = await Customer.findById(customerID);

    if (!customer) {
      return res
        .status(404)
        .json({ message: "Không tìm thấy khách hàng tương ứng với ID." });
    }

    await Customer.deposit(customer.CustomerID, amount);
    res.json({ message: "Nạp tiền thành công" });
  }),

  ResetPassword: asyncHandler(async (req, res) => {
    const { email, newPassword } = req.body;

    if (!email || !newPassword) {
      return res
        .status(400)
        .json({ message: "Thiếu thông tin email hoặc mật khẩu mới." });
    }

    const customer = await Customer.findByEmail(email);
    if (!customer) {
      return res
        .status(404)
        .json({ message: "Không tìm thấy tài khoản tương ứng với email." });
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await Customer.updatePassword(email, hashedPassword);

    res.json({ message: "Mật khẩu đã được cập nhật" });
  }),

  GetBalance: asyncHandler(async (req, res) => {
    const { customerID } = req.params;

    if (!customerID)
      return res.status(400).json({ message: "Thiếu thông tin customerID." });

    const balance = await Customer.getBalance(customerID);

    if (balance === null)
      return res
        .status(404)
        .json({ message: "Không tìm thấy khách hàng tương ứng." });

    res.json({ customerID, balance });
  }),
};

module.exports = customerController;
