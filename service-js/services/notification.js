const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const asyncHandler = require("express-async-handler");
const nodemailer = require("nodemailer");

// Configure nodemailer transporter (using environment variables or defaults)
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

const notificationController = {
    // Send OTP Email
    SendEmail: asyncHandler(async (req, res) => {
        const { to, subject, text, html } = req.body;

        // if (!to || !subject || !text) {
        //     return res.status(400).json({ message: "Missing required fields (to, subject, text)" });
        // }

        const mailOptions = {
        from: process.env.SMTP_USER,
        to,
        subject,
        text,
        ...(html && { html }),
        };

        try {
            await transporter.sendMail(mailOptions);
            res.json({
                message: "Notification sent to your email. Please check your email.",
            });
        } catch (error) {
            console.error("Error sending recovery email:", error);
            res.status(500).json({ message: "Failed to send notification to your email." });
        }
    }),
}

module.exports = notificationController;