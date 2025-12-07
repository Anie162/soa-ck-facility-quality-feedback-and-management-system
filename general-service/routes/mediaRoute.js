const express = require("express");
const router = express.Router();
const { mediaService, upload } = require("../services/media");

/**
 * @openapi
 * /api/media/upload:
 *   post:
 *     tags: [Media]
 *     summary: Upload file (ảnh hoặc video) lên Cloudinary và lưu thông tin vào MongoDB
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               file:
 *                 type: string
 *                 format: binary
 *     responses:
 *       200:
 *         description: Upload thành công
 */
router.post("/upload", upload.single("file"), mediaService.UploadFile);

/**
 * @openapi
 * /api/media/{mediaId}:
 *   get:
 *     tags: [Media]
 *     summary: Lấy URL file từ Cloudinary bằng mediaId
 *     parameters:
 *       - in: path
 *         name: mediaId
 *         required: true
 *         schema:
 *           type: string
 *         description: Cloudinary mediaId của file
 *     responses:
 *       200:
 *         description: Trả về URL của file
 */
router.get("/:mediaId", mediaService.GetFile);

/**
 * @openapi
 * /api/media/{mediaId}:
 *   delete:
 *     tags: [Media]
 *     summary: Xóa file media trên Cloudinary bằng mediaId và xóa thông tin trong MongoDB
 *     parameters:
 *       - in: path
 *         name: mediaId
 *         required: true
 *         schema:
 *           type: string
 *         description: Cloudinary mediaId của file
 *     responses:
 *       200:
 *         description: Xóa file thành công
 */
router.delete("/:mediaId", mediaService.DeleteFile);

module.exports = router;
