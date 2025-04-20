const nodemailer = require('nodemailer');
const dotenv = require('dotenv');
dotenv.config();

console.log('SMTP_USER:', process.env.SMTP_USER); // Kiểm tra lại biến môi trường
console.log('SMTP_PASS:', process.env.SMTP_PASS);

const transporter = nodemailer.createTransport({
    host: "smtp-relay.brevo.com",
    port: process.env.SMTP_PORT,
    secure: false, // true for 465, false for 587
    auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
    },
    logger: true,
    debug: true
});
module.exports = transporter;