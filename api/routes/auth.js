const router = require("express").Router();
const User = require("../models/User");
let CryptoJS = require("crypto-js");
const jwt = require("jsonwebtoken");
const crypto = require('crypto');
const {
    sendPasswordResetEmail,
    sendResetSuccessEmail,
    sendVerificationEmail,
    sendWelcomeEmail,
} = require("../mailtrap/email");

//REGISTER
router.post("/register", async (req, res) => {
    {
        const {email, password, username} = req.body;
        if (!email || !password || !username) {
            return res.status(400).json({success: false, message: "All fields are required"});
        }
    }
    const verificationToken = Math.floor(100000 + Math.random() * 900000).toString();

    const newUser = new User({
        username: req.body.username,
        email: req.body.email,
        password: CryptoJS.AES.encrypt(req.body.password, process.env.SECRET_KEY).toString(),
        verificationToken: verificationToken,
        verificationTokenExpiresAt: Date.now() + 24 * 60 * 60 * 1000,
    });

    try {
        const user = await newUser.save();
        await sendVerificationEmail(newUser.email, verificationToken);
        res.status(201).json({
            user: {
        ...user._doc,
                password: undefined,
        },
    });

    }
    catch (err) {
        res.status(500).json(err);
    }
})

//LOGIN
router.post("/login", async (req, res) => {
    try {
        const user = await User.findOne({ email: req.body.email });
        if (!user) {
            return res.status(404).json("Wrong password or username!");
        }
        let bytes = CryptoJS.AES.decrypt(user.password, process.env.SECRET_KEY);
        const originalPassword = bytes.toString(CryptoJS.enc.Utf8);

        if (originalPassword !== req.body.password) {
            return res.status(404).json("Wrong password or username!");
        }

        const accessToken = jwt.sign({ id: user._id, isAdmin: user.isAdmin ,
                //lastPasswordChange: user.lastPasswordChange.getTime()
            },
            process.env.SECRET_KEY,
            { expiresIn: '5d' });

        const { password, ...info } = user._doc;

        res.status(200).json({ ...info, accessToken });
    }
    catch (err) {
        res.status(500).json(err);
    }
})

router.post("/verify-email", async (req, res) => {
    console.log("Verify email");
    const { code } = req.body;
    try {
        const user = await User.findOne({
            verificationToken: code,
            verificationTokenExpiresAt: { $gt: Date.now() },
        });

        if (!user) {
            return res.status(400).json({ success: false, message: "Invalid or expired verification code" });
        }
        const accessToken = jwt.sign({ id: user._id, isAdmin: user.isAdmin }, process.env.SECRET_KEY, { expiresIn: '5d' });
        user.isVerified = true;
        user.verificationToken = undefined;
        user.verificationTokenExpiresAt = undefined;
        await user.save();

        await sendWelcomeEmail(user.email, user.name);

        res.status(200).json({
            success: true,
            message: "Email verified successfully",
            user: {
                ...user._doc,
                password: undefined,
            },
            accessToken,
        });
    } catch (error) {
        console.log("error in verifyEmail ", error);
        res.status(500).json({ success: false, message: "Server error" });
    }
})

router.post("/forgot-password", async (req, res) => {
    const { email } = req.body;
    console.log("Sending reset email to:", email);
    try {
        const user = await User.findOne({ email });

        if (!user) {
            return res.status(400).json({ success: false, message: "User not found" });
        }

        // Generate reset token
        const resetToken = crypto.randomBytes(20).toString("hex");
        const resetTokenExpiresAt = Date.now() + 1 * 60 * 60 * 1000; // 1 hour

        user.resetPasswordToken = resetToken;
        user.resetPasswordExpiresAt = resetTokenExpiresAt;

        await user.save();

        // send email
        console.log(process.env.CLIENT_URL);
        await sendPasswordResetEmail(user.email, `${process.env.CLIENT_URL}/reset-password/${resetToken}`);

        res.status(200).json({ success: true, message: "Password reset link sent to your email" });
    } catch (error) {
        console.log("Error in forgotPassword ", error);
        res.status(400).json({ success: false, message: error.message });
    }
})

router.post("/reset-password/:token", async (req, res) => {
        try {
            const { token } = req.params;
            const { password } = req.body;

            const user = await User.findOne({
                resetPasswordToken: token,
                resetPasswordExpiresAt: { $gt: Date.now() },
            });

            if (!user) {
                return res.status(400).json({ success: false, message: "Invalid or expired reset token" });
            }

            // update password
      //      const hashedPassword = await bcryptjs.hash(password, 10);
            const hashedPassword = CryptoJS.AES.encrypt(req.body.password, process.env.SECRET_KEY).toString();
            user.password = hashedPassword;
            user.resetPasswordToken = undefined;
            user.resetPasswordExpiresAt = undefined;
           // user.lastPasswordChange = new Date();
            await user.save();

            await sendResetSuccessEmail(user.email);

            res.status(200).json({ success: true, message: "Password reset successful" });
        } catch (error) {
            console.log("Error in resetPassword ", error);
            res.status(400).json({ success: false, message: error.message });
        }

})

module.exports = router;