import "./searchcard.scss";
import {useState, useEffect} from "react";
import axios from "axios";
import Button from "@mui/material/Button";
import FavoriteIcon from "@mui/icons-material/Favorite";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import InfoIcon from "@mui/icons-material/Info";
import {Link} from "react-router-dom";

function Popup({movie}) {
    return (
        <div className="movie-popup">
            <div className="popup-poster-wrapper">
                <img
                    className="popup-poster"
                    src={movie.imgSm}
                    alt={movie.title}
                />
            </div>

            <div className="popup-info">
                <h3>{movie.title}</h3>

                <div className="popup-buttons">
                    <Link to={{pathname: "/watch"}} state={{movie: movie}}>

                        <Button
                            className="watch-btn"
                            size="small"
                            color="red"
                            startIcon={<PlayArrowIcon fontSize="inherit"/>}
                        >
                            Xem ngay
                        </Button>
                    </Link>
                    <Button
                        className="like"
                        variant="outlined"
                        size="small"
                        color="neutral"
                        startIcon={<FavoriteIcon fontSize="inherit"/>}
                    >
                        Thích
                    </Button>
                    <Link to={{pathname: "/movie"}} state={{movie: movie}}>
                    <Button
                        className="info"
                        variant="outlined"
                        size="small"
                        color="neutral"
                        startIcon={<InfoIcon fontSize="inherit"/>}
                    >
                        Chi tiết
                    </Button>
                    </Link>
                </div>

                <div className="popup-meta">
                    <span className="item">{movie.duration}</span>
                    <span className="limit">+{movie.limit}</span>
                    <span className="item">{movie.year}</span>
                    <div className="genre">{movie.genre}</div>
                    <span>HD</span>
                </div>
            </div>
        </div>

    );
}

export default function SearchCard({movieId}) {
    const [movie, setMovie] = useState({});

    useEffect(() => {
        const getMovie = async () => {
            try {
                const res = await axios.get(`/api/movies/${movieId}`, {
                    headers: {
                        token:
                            "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setMovie(res.data);
            } catch (error) {
                console.log(error);
            }
        };
        getMovie();
    }, [movieId]);
    return (
        <div className="search-card-wrapper">
            <div className="search-card">
                <img
                    className="movie-thumbnail"
                    src={movie.imgSm}
                    alt={movie.title}
                />
                <h3>{movie.title}</h3>
            </div>
            <Popup movie={movie}/>
        </div>
    );
}
