import { motion } from "framer-motion";
import "./LoadingSpinner.scss"; // Import CSS thuần

const LoadingSpinner = () => {
    return (
        <div className="popup">
            <motion.div
                className="spinner"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
        </div>
    );
};

export default LoadingSpinner;
