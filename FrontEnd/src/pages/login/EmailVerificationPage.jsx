import {useContext, useEffect, useRef, useState} from "react";
import { useNavigate } from "react-router-dom";
import "./verification.scss";
import { AuthContext } from "../../authContext/AuthContext";
import {verifyEmail} from "../../authContext/apiCalls.js";
const EmailVerificationPage = () => {
    const [code, setCode] = useState(["", "", "", "", "", ""]);
    const inputRefs = useRef([]);
    const navigate = useNavigate();
    const {error,isFetching, isEmailVerified, dispatch } = useContext(AuthContext);

    const handleChange = (index, value) => {
        const newCode = [...code];

        // Handle pasted content
        if (value.length > 1) {
            const pastedCode = value.slice(0, 6).split("");
            for (let i = 0; i < 6; i++) {
                newCode[i] = pastedCode[i] || "";
            }
            setCode(newCode);

            // Focus on the last non-empty input or the first empty one
            const lastFilledIndex = newCode.findLastIndex((digit) => digit !== "");
            const focusIndex = lastFilledIndex < 5 ? lastFilledIndex + 1 : 5;
            inputRefs.current[focusIndex].focus();
        } else {
            newCode[index] = value;
            setCode(newCode);

            // Move focus to the next input field if value is entered
            if (value && index < 5) {
                inputRefs.current[index + 1].focus();
            }
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === "Backspace" && !code[index] && index > 0) {
            inputRefs.current[index - 1].focus();
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const verificationCode = code.join("");
        try {
            await verifyEmail(verificationCode, dispatch, navigate);
             navigate("/");
        } catch (e) {
            console.error(e);
        }
    };

    // Auto submit when all fields are filled
    useEffect(() => {
        if (code.every((digit) => digit !== "")) {
            handleSubmit(new Event("submit"));
        }
    }, [code]);
    return (
        <div className="container">
            <div className="inner">
                <h2 className="title">Verify Your Email</h2>
                <p className="subtitle">Enter the 6-digit code sent to your email address.</p>

                <form onSubmit={handleSubmit} className="form">
                    <div className="codeInputs">
                        {code.map((digit, index) => (
                            <input
                                key={index}
                                ref={(el) => (inputRefs.current[index] = el)}
                                type='text'
                                maxLength='1'
                                value={digit}
                                onChange={(e) => handleChange(index, e.target.value)}
                                onKeyDown={(e) => handleKeyDown(index, e)}
                            />
                        ))}
                    </div>

                    {error && <p className="error">{error}</p>}

                    <button
                        type='submit'
                        disabled={isFetching || code.some((digit) => !digit)}
                        className="button"
                    >
                        {isFetching ? "Verifying..." : "Verify Email"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default EmailVerificationPage;
