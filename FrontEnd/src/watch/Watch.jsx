import { Link, useLocation } from "react-router-dom";
import "./watch.scss"
import { ArrowBackOutlined } from "@mui/icons-material";

export default function Watch() {
    const location = useLocation();
    const movie = location.state.movie;
    return (
        <div className="watch">
            <Link to="/">

                <div className="back">
                    <ArrowBackOutlined />
                    Home
                </div>
            </Link>
            {/* <video
                className="video"
                autoPlay
                progress
                controls
                // src={movie.video}
                src="https://vip.opstream16.com/share/7362b26d78069dd38f4b45743fddc7ee"
            /> */}
            <iframe className="video" src={movie.video} allowFullScreen></iframe>
        </div>
    )
}