const { pool, sql } = require("../configs/database");
const { v4: uuidv4 } = require("uuid");

class Customer {
  constructor({ CustomerID, CustomerFullName, CustomerEmail, CustomerPhone, CustomerPassword, CustomerBalance }) {
    this.id = CustomerID;
    this.fullName = CustomerFullName;
    this.email = CustomerEmail;
    this.phone = CustomerPhone;
    this.password = CustomerPassword;
    this.balance = CustomerBalance;
  }

  static fromRecord(record) {
    return new Customer(record);
  }

  // Tìm khách hàng theo email
  static async findByEmail(email) {
    const result = await pool.request()
      .input("Email", sql.NVarChar(100), email)
      .query("SELECT * FROM Customer WHERE CustomerEmail = @Email");

    if (result.recordset.length === 0) return null;
    return Customer.fromRecord(result.recordset[0]);
  }

  // Tìm khách hàng theo ID
  static async findById(id) {
    const result = await pool.request()
      .input("CustomerID", sql.VarChar(255), id)
      .query("SELECT * FROM Customer WHERE CustomerID = @CustomerID");

    if (result.recordset.length === 0) return null;
    return Customer.fromRecord(result.recordset[0]);
  }

  // Đăng ký khách hàng mới với UUID
  static async create({ fullName, phone, email, password, balance = 0 }) {
    const newId = uuidv4();
 
    await pool.request()
      .input("CustomerID", sql.VarChar(255), newId)
      .input("FullName", sql.NVarChar(100), fullName)
      .input("Phone", sql.Char(10), phone)
      .input("Email", sql.NVarChar(100), email)
      .input("Password", sql.VarChar(255), password)
      .input("Balance", sql.Decimal(12, 2), balance)
      .query(`
        INSERT INTO Customer (CustomerID, CustomerFullName, CustomerPhone, CustomerEmail, CustomerPassword, CustomerBalance)
        VALUES (@CustomerID, @FullName, @Phone, @Email, @Password, @Balance)
      `);

    return newId;
  }

  // Cập nhật mật khẩu
  static async updatePassword(email, hashedPassword) {
    await pool.request()
      .input("Email", sql.NVarChar(100), email)
      .input("Password", sql.VarChar(255), hashedPassword)
      .query("UPDATE Customer SET CustomerPassword = @Password WHERE CustomerEmail = @Email");
  }

  // Rút tiền
  static async withdraw(id, amount) {
    await pool.request()
      .input("CustomerID", sql.VarChar(255), id)
      .input("Amount", sql.Decimal(12, 2), amount)
      .query("UPDATE Customer SET CustomerBalance = CustomerBalance - @Amount WHERE CustomerID = @CustomerID");
  }

  // Nạp tiền
  static async deposit(id, amount) {
    await pool.request()
      .input("CustomerID", sql.VarChar(255), id)
      .input("Amount", sql.Decimal(12, 2), amount)
      .query("UPDATE Customer SET CustomerBalance = CustomerBalance + @Amount WHERE CustomerID = @CustomerID");
  }

  // Lấy số dư tài khoản theo ID
  static async getBalance(id) {
    const result = await pool.request()
      .input("CustomerID", sql.VarChar(255), id)
      .query("SELECT CustomerBalance FROM Customer WHERE CustomerID = @CustomerID");

    if (result.recordset.length === 0) return null;
    return result.recordset[0].CustomerBalance;
  }
}

module.exports = Customer;
