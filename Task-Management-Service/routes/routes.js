// Task-Management-Service/routes.js
const express = require("express");
const taskService = require("../services/task");

const router = express.Router();

/**
 * @openapi
 * tags:
 *   - name: Task
 *     description: Quản lý Task xử lí Report (giao việc, cập nhật trạng thái)
 */

/**
 * @openapi
 * /api/tasks:
 *   post:
 *     tags: [Task]
 *     summary: Tạo task mới
 *     description: "Tạo một task mới dựa trên báo cáo (report) hoặc yêu cầu xử lí."
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - title
 *               - createdBy
 *             properties:
 *               reportId:
 *                 type: string
 *                 description: ID của report liên quan (nếu có)
 *               createdBy:
 *                 type: string
 *                 description: ID user tạo task
 *               assignedTo:
 *                 type: string
 *                 description: ID user được giao xử lí
 *               title:
 *                 type: string
 *               description:
 *                 type: string
 *               deadline:
 *                 type: string
 *                 format: date-time
 *     responses:
 *       201:
 *         description: Tạo task thành công
 */
router.post("/tasks", taskService.CreateTask);

/**
 * @openapi
 * /api/tasks:
 *   get:
 *     tags: [Task]
 *     summary: Lấy danh sách task
 *     parameters:
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *         description: Lọc theo trạng thái task
 *       - in: query
 *         name: assignedTo
 *         schema:
 *           type: string
 *         description: Lọc theo người được giao
 *       - in: query
 *         name: createdBy
 *         schema:
 *           type: string
 *         description: Lọc theo người tạo
 *     responses:
 *       200:
 *         description: Danh sách task
 */
router.get("/tasks", taskService.GetTasks);

/**
 * @openapi
 * /api/tasks/{id}:
 *   get:
 *     tags: [Task]
 *     summary: Lấy chi tiết 1 task
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID của task
 *     responses:
 *       200:
 *         description: Chi tiết task
 *       404:
 *         description: Không tìm thấy task
 */
router.get("/tasks/:id", taskService.GetTaskById);

/**
 * @openapi
 * /api/tasks/{id}:
 *   put:
 *     tags: [Task]
 *     summary: Cập nhật thông tin task
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID của task
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               title: { type: string }
 *               description: { type: string }
 *               assignedTo: { type: string }
 *               deadline:
 *                 type: string
 *                 format: date-time
 *     responses:
 *       200:
 *         description: Cập nhật thành công
 *       404:
 *         description: Không tìm thấy task
 */
router.put("/tasks/:id", taskService.UpdateTask);

/**
 * @openapi
 * /api/tasks/{id}/status:
 *   patch:
 *     tags: [Task]
 *     summary: Cập nhật trạng thái task
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID của task
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - status
 *             properties:
 *               status:
 *                 type: string
 *                 description: "Trạng thái mới của task (PENDING, PROCESSING, SUCCESS, FAILED_STANDARD, ...)"
 *               reason:
 *                 type: string
 *                 description: "Lý do (nếu từ chối / không đạt tiêu chuẩn)"
 *               isFailedStandard:
 *                 type: boolean
 *                 description: "Đánh dấu Không đạt tiêu chuẩn"
 *               changedBy:
 *                 type: string
 *                 description: "ID người thay đổi trạng thái"
 *     responses:
 *       200:
 *         description: Cập nhật trạng thái thành công
 *       400:
 *         description: Trạng thái không hợp lệ
 *       404:
 *         description: Không tìm thấy task
 */
router.patch("/tasks/:id/status", taskService.UpdateTaskStatus);

module.exports = router;
