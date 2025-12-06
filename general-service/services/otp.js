const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const asyncHandler = require("express-async-handler");

// In-memory store for OTPCode: email -> { code, expires }
const otpCodes = new Map();

const otpController = {
  // Issue OTP
  SendOTP: asyncHandler(async (req, res) => {
    const { email } = req.body;

    if (otpCodes.has(email)) otpCodes.delete(email);

    // Generate 6-digit recovery code
    const code = Math.floor(100000 + Math.random() * 900000).toString();

    // Store code with expiration (5 minutes)
    const expires = Date.now() + 5 * 60 * 1000;

    otpCodes.set(email, { code, expires });

    // Send OTP to email  - > Call Notification Service
    try {
      await fetch("http://localhost:8000/api/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            to: email,
            subject: "Tuition Payment Verification – Your OTP Code",
            text: `Your OTP for verifying tuition payment is: ${code}. It will expire in 5 minutes.\n
                Please confirm your identity by entering this 6-digit code to verify your tuition payment.
                Just a heads up: this code will expire in 5 minutes for security reasons.`,
            html: `
            <div style="font-family: Arial, sans-serif; text-align: center; padding: 10px; color: #333;">
                <h2 style="margin-bottom: 10px; color: #2c3e50;">Your OTP Code is</h2>

                <div style="font-size: 32px; font-weight: bold; color: #000000ff; margin: 10px 0;">
                ${code}
                </div>

                <p style="font-size: 14px; line-height: 1.6; max-width: 500px; margin: 0 auto 5px auto; text-align: center; color: #555;">
                Please confirm your identity by entering this 6-digit code to verify your tuition payment. 
                Just a heads up: this code will expire in 5 minutes for security reasons.
                </p>
            </div>
            `,
        }),
      })  

      res.json({
        message: "OTP code sent to your email",
      });
    } catch (error) {
      console.error("Error calling Notification Service:", error.message);
      res.status(500).json({ message: "Failed to send OTP to email." });
    }
  }),

  // Verify OTP
  VerifyOTP: asyncHandler(async (req, res) => {
    const { email, code } = req.body;

    if (!email || !code) {
        return res.status(400).json({
            success: false,
            error: { code: "MISSING_FIELDS", message: "Hãy điền mã OTP của bạn." }
        });
    }

    const record = otpCodes.get(email);
    if (!record) {
        // Option: for security, you can return same message as INVALID_OTP
        return res.status(404).json({
            success: false,
            error: { code: "OTP_NOT_FOUND", message: "No OTP found for this email." }
        });
    }

    if (record.expires < Date.now()) {
        otpCodes.delete(email);
        return res.status(410).json({
            success: false,
            error: { code: "OTP_EXPIRED", message: "OTP hết hạn." }
        });
    }

    // const isMatch = await bcrypt.compare();

    if (record.code !== code) {
        return res.status(401).json({
            success: false,
            error: { code: "INVALID_OTP", message: "OTP không đúng." }
        });
    }

    // If code is valid, delete it to prevent reuse
    otpCodes.delete(email);
    return res.status(200).json({ success: true, message: "OTP verified" });
  }),
}

module.exports = otpController;