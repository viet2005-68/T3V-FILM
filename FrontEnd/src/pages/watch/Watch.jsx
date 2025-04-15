import { Link, useLocation } from "react-router-dom";
import "./watch.scss"
import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";

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
            <iframe className="video" src={movie.video} allowFullScreen  title="video"></iframe>
        </div>
    )
}