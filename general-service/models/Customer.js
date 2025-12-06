const mongoose = require("mongoose");
const { v4: uuidv4 } = require("uuid");

const customerSchema = new mongoose.Schema(
  {
    CustomerID: { type: String, default: uuidv4 },
    CustomerFullName: { type: String, required: true },
    CustomerEmail: { type: String, required: true, unique: true },
    CustomerPhone: { type: String, required: true },
    CustomerPassword: { type: String, required: true },
    CustomerBalance: { type: Number, default: 0 },
  },
  { versionKey: false }
);

// =============================
// Static methods (giữ API giống SQL Server version)
// =============================
customerSchema.statics.findByEmail = function (email) {
  return this.findOne({ CustomerEmail: email });
};

customerSchema.statics.findById = function (id) {
  return this.findOne({ CustomerID: id });
};

customerSchema.statics.createCustomer = async function ({
  fullName,
  phone,
  email,
  password,
  balance = 0,
}) {
  const customer = new this({
    CustomerFullName: fullName,
    CustomerPhone: phone,
    CustomerEmail: email,
    CustomerPassword: password,
    CustomerBalance: balance,
  });

  await customer.save();
  return customer.CustomerID;
};

customerSchema.statics.updatePassword = function (email, hashedPassword) {
  return this.updateOne(
    { CustomerEmail: email },
    { CustomerPassword: hashedPassword }
  );
};

customerSchema.statics.withdraw = function (id, amount) {
  return this.updateOne(
    { CustomerID: id },
    { $inc: { CustomerBalance: -amount } }
  );
};

customerSchema.statics.deposit = function (id, amount) {
  return this.updateOne(
    { CustomerID: id },
    { $inc: { CustomerBalance: amount } }
  );
};

customerSchema.statics.getBalance = async function (id) {
  const customer = await this.findOne({ CustomerID: id });
  return customer ? customer.CustomerBalance : null;
};

module.exports = mongoose.model("Customer", customerSchema);
