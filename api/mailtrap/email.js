const {
    PASSWORD_RESET_REQUEST_TEMPLATE,
    PASSWORD_RESET_SUCCESS_TEMPLATE,
    VERIFICATION_EMAIL_TEMPLATE,
    WELCOME_EMAIL_TEMPLATE,
} = require("./emailTemplates.js");

const  transporter = require("./nodemailer.js");

 const sendVerificationEmail = async (email, verificationToken) => {
//	const recipient = [{ email }];

    try {
        const info = await transporter.sendMail({
            from: '"T3V FilmWebPro" <tungq2005@gmail.com>',
            to: email,
            subject: "Xác minh email của bạn",
            html: VERIFICATION_EMAIL_TEMPLATE.replace("{verificationCode}", verificationToken),
            category: "Email Verification",
        });
        console.log("Email sent: " + info.messageId);
    } catch (error) {
        console.error("Lỗi gửi email:", error);
    }
};

 const sendWelcomeEmail = async (email, name) => {
//	const recipient = [{ email }];

    try {
        const info = await transporter.sendMail({
            from: '"T3V FilmWebPro" <tungq2005@gmail.com>',
            to: email,
            subject: "Chao ban",
            html: WELCOME_EMAIL_TEMPLATE
        });

        console.log("Welcome email sent successfully", info.messageId);
    } catch (error) {
        console.error(`Error sending welcome email`, error);

        throw new Error(`Error sending welcome email: ${error}`);
    }
};
//
// export const sendPasswordResetEmail = async (email, resetURL) => {
// 	const recipient = [{ email }];
//
// 	try {
// 		const response = await mailtrapClient.send({
// 			from: sender,
// 			to: recipient,
// 			subject: "Reset your password",
// 			html: PASSWORD_RESET_REQUEST_TEMPLATE.replace("{resetURL}", resetURL),
// 			category: "Password Reset",
// 		});
// 	} catch (error) {
// 		console.error(`Error sending password reset email`, error);
//
// 		throw new Error(`Error sending password reset email: ${error}`);
// 	}
// };


 const sendPasswordResetEmail = async (email, resetURL) => {
//	const recipient = [{ email }];

    try {
        const info = await transporter.sendMail({
            from: '"T3V FilmWebPro" <tungq2005@gmail.com>',
            to: email,
            subject: "Reset your password",
            html: PASSWORD_RESET_REQUEST_TEMPLATE.replace("{resetURL}", resetURL),
            category: "Password Reset",
        });
    } catch (error) {
        console.error(`Error sending password reset email`, error);

        throw new Error(`Error sending password reset email: ${error}`);
    }
};

// export const sendResetSuccessEmail = async (email) => {
// 	const recipient = [{ email }];
//
// 	try {
// 		const response = await mailtrapClient.send({
// 			from: sender,
// 			to: recipient,
// 			subject: "Password Reset Successful",
// 			html: PASSWORD_RESET_SUCCESS_TEMPLATE,
// 			category: "Password Reset",
// 		});
//
// 		console.log("Password reset email sent successfully", response);
// 	} catch (error) {
// 		console.error(`Error sending password reset success email`, error);
//
// 		throw new Error(`Error sending password reset success email: ${error}`);
// 	}
// };

 const sendResetSuccessEmail = async (email) => {
//	const recipient = [{ email }];

    try {
        const info = await transporter.sendMail({
            from: '"T3V FilmWebPro" <tungq2005@gmail.com>',
            to: email,
            subject: "Password Reset Successful",
            html: PASSWORD_RESET_SUCCESS_TEMPLATE,
            category: "Password Reset",
        });

        console.log("Password reset email sent successfully", info.messageId);
    } catch (error) {
        console.error(`Error sending password reset success email`, error);

        throw new Error(`Error sending password reset success email: ${error}`);
    }
};

module.exports = {
    sendVerificationEmail,
    sendWelcomeEmail,
    sendPasswordResetEmail,
    sendResetSuccessEmail,
};
