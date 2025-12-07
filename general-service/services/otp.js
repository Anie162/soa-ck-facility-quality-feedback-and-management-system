const asyncHandler = require("express-async-handler");

const otpStore = new Map();
// key: `${email}:${action}`
// value: { code, expires }

const otpController = {
  // Issue OTP
  SendOTP: asyncHandler(async (req, res) => {
    const { email, action } = req.body;

    if (!email || !action) {
      return res.status(400).json({
        success: false,
        message: "Missing email or action",
      });
    }

    const key = `${email}:${action}`;
    otpStore.delete(key); // xoá OTP cũ

    // Create OTP
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const expires = Date.now() + 5 * 60 * 1000; // 5 phút

    otpStore.set(key, { code, expires });

    // Send email by Notification Service
    try {
      await fetch("http://localhost:8000/api/email/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: email,
          subject: `Your OTP Code for ${action}`,
          text: `Your OTP is ${code}. It expires in 5 minutes.`,
          html: `<p>Your OTP is <b>${code}</b>. It expires in 5 minutes.</p>`,
        }),
      });

      res.json({ success: true, message: "OTP sent to email" });
    } catch (error) {
      console.error("Error calling Notification service:", error);
      res.status(500).json({ success: false, message: "Send OTP failed" });
    }
  }),

  // Verify OTP
  VerifyOTP: asyncHandler(async (req, res) => {
    const { email, action, code } = req.body;

    if (!email || !action || !code) {
      return res.status(400).json({
        success: false,
        message: "Missing email, action, or code",
      });
    }

    const key = `${email}:${action}`;
    const record = otpStore.get(key);

    if (!record) {
      return res.status(404).json({
        success: false,
        message: "OTP not found for this action",
      });
    }

    if (record.expires < Date.now()) {
      otpStore.delete(key);
      return res.status(410).json({
        success: false,
        message: "OTP expired",
      });
    }

    if (record.code !== code) {
      return res.status(401).json({
        success: false,
        message: "Invalid OTP",
      });
    }

    // Valid → delete OTP
    otpStore.delete(key);

    res.json({
      success: true,
      message: "OTP verified successfully",
    });
  }),
};

module.exports = otpController;