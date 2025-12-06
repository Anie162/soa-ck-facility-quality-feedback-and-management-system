const express = require("express");
const otpController = require("../services/otp");
const notificationController = require("../services/notification");
const customerService = require("../services/customer");

const router = express.Router();

/**
 * @openapi
 * tags:
 *   - name: OTP
 *     description: Gửi và xác thực mã OTP
 *   - name: Notification
 *     description: Gửi email thông báo
 *   - name: User
 *     description: Quản lý tài khoản User (Người báo cáo, Nhân viên tiếp nhận và điều phối xử lí, Nhân viên kỹ thuật tại hiện trường) và phân quyền cho từng người dùng
 */

/**
 * @openapi
 * /api/send-otp:
 *   post:
 *     tags: [OTP]
 *     summary: Gửi mã OTP qua email
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *     responses:
 *       200:
 *         description: OTP đã được gửi đến email
 */
router.post("/send-otp", otpController.SendOTP);

/**
 * @openapi
 * /api/verify-otp:
 *   post:
 *     tags: [OTP]
 *     summary: Xác thực mã OTP
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *               code:
 *                 type: string
 *     responses:
 *       200:
 *         description: OTP hợp lệ
 *       401:
 *         description: OTP sai hoặc hết hạn
 */
router.post("/verify-otp", otpController.VerifyOTP);

/**
 * @openapi
 * /api/send-email:
 *   post:
 *     tags: [Notification]
 *     summary: Gửi email thông báo
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               to:
 *                 type: string
 *               subject:
 *                 type: string
 *               text:
 *                 type: string
 *               html:
 *                 type: string
 *     responses:
 *       200:
 *         description: Gửi email thành công
 */
router.post("/send-email", notificationController.SendEmail);


/**
 * @openapi
 * /api/customers/register:
 *   post:
 *     tags: [User]
 *     summary: Đăng ký tài khoản khách hàng
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               fullName: { type: string }
 *               phone: { type: string }
 *               email: { type: string }
 *               password: { type: string }
 *     responses:
 *       200:
 *         description: Đăng ký thành công
 */
router.post("/customers/register", customerService.Register);

/**
 * @openapi
 * /api/customers/login:
 *   post:
 *     tags: [User]
 *     summary: Đăng nhập tài khoản khách hàng
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email: { type: string }
 *               password: { type: string }
 *     responses:
 *       200:
 *         description: Đăng nhập thành công, trả về token
 */
router.post("/customers/login", customerService.Login);

/**
 * @openapi
 * /api/customers/withdraw:
 *   post:
 *     tags: [User]
 *     summary: Rút tiền từ tài khoản khách hàng
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               customerId: { type: string }
 *               amount: { type: number }
 *     responses:
 *       200:
 *         description: Rút tiền thành công
 */
router.post("/customers/withdraw", customerService.Withdraw);

/**
 * @openapi
 * /api/customers/deposit:
 *   post:
 *     tags: [User]
 *     summary: Nạp tiền vào tài khoản khách hàng bằng email
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               customerEmail: { type: string }
 *               amount: { type: number }
 *     responses:
 *       200:
 *         description: Nạp tiền thành công
 */
router.post("/customers/deposit", customerService.Deposit);

/**
 * @openapi
 * /api/customers/deposit-with-id:
 *   post:
 *     tags: [User]
 *     summary: Nạp tiền vào tài khoản khách hàng bằng ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               customerID: { type: string }
 *               amount: { type: number }
 *     responses:
 *       200:
 *         description: Nạp tiền thành công
 */
router.post("/customers/deposit-with-id", customerService.DepositWithID);

/**
 * @openapi
 * /api/customers/reset-password:
 *   post:
 *     tags: [User]
 *     summary: Đặt lại mật khẩu cho tài khoản khách hàng
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email: { type: string }
 *               newPassword: { type: string }
 *     responses:
 *       200:
 *         description: Cập nhật mật khẩu thành công
 */
router.post("/customers/reset-password", customerService.ResetPassword);

/**
 * @openapi
 * /api/customers/balance/{customerID}:
 *   get:
 *     tags: [User]
 *     summary: Lấy số dư tài khoản khách hàng
 *     parameters:
 *       - name: customerID
 *         in: path
 *         required: true
 *         schema: { type: string }
 *     responses:
 *       200:
 *         description: Trả về số dư tài khoản
 */
router.get("/customers/balance/:customerID", customerService.GetBalance);

module.exports = router;

// http://localhost:8000/api/customers/