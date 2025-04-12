import "./movie.scss"
import { useLocation } from "react-router-dom"
import Navbar from "../../components/navbar/Navbar"
import { FavoriteBorder, Favorite, PlayArrow, Add, Share, Stars, Comment, Notes, PlayArrowOutlined } from "@mui/icons-material";
import { Link } from "react-router-dom";

export default function Movie() {
    const location = useLocation()
    const movie = location.state.movie
    console.log(movie)
    const calculateRating = (reviews) => {
        let avg = 0
        for (let review of reviews) {
            avg += review.rating
        }
        return avg / (reviews.length !== 0 ? reviews.length : 1)
    }

    return (
        <>
            <Navbar />
            <div
                style={{ backgroundImage: `linear-gradient(to bottom, rgba(0, 0, 0, 0.2) 0%, var(--main-color) 100%), url("${movie.img}")`, }}
                className="movie"
            >
            </div>
            <div className="movieContainer">
                <div className="movieContainerLeft">
                    <img src={movie.imgSm} alt="" />
                    <h1>{movie.title}</h1>
                    <div className="tags">
                        <span style={{ backgroundColor: "white", color: "black" }}>{movie.limit}+</span>
                        <span>{movie.year}</span>
                        <span>{movie.genre}</span>
                    </div>
                    <div className="movieInfo">
                        <h3>Description:</h3>
                        <p>{movie.desc}</p>
                    </div>
                    <div className="movieInfo">
                        <p><b style={{ fontSize: "20px", marginRight: "10px" }}>Duration: </b>{movie.duration}</p>
                    </div>
                </div>
                <div className="movieContainerRight">
                    <div className="containerTop">
                        <div className="buttonGroup">
                            <Link className="link" to={{ pathname: "/watch" }} state={{ movie: movie }}>
                                <div className="movieButton">
                                    <PlayArrow />
                                    Watch Now
                                </div>
                            </Link>
                            <div className="movieButton">
                                <Favorite />
                                Favorite
                            </div>
                            <div className="movieButton">
                                <Add />
                                Add
                            </div>
                            <div className="movieButton">
                                <Share />
                                Share
                            </div>
                            <div className="movieButton">
                                <Comment />
                                Comment
                            </div>
                        </div>
                        <div className="movieRating">
                            <Stars />
                            <h3>{calculateRating(movie.reviews)}</h3>
                            <p>Rate Now</p>
                        </div>
                    </div>
                    <div className="containerMid">
                        <div className="containerDesc">
                            <Notes />
                            <h3>Episodes</h3>
                        </div>
                        <ul>
                            <Link className="link" to={{ pathname: "/watch" }} state={{ movie: movie }}>
                                <li>Ep 1</li>
                            </Link>
                        </ul>
                    </div>

                    <div className="containerMid">
                        <div className="containerDesc">
                            <Comment />
                            <h3>Comments ({movie.reviews.length})</h3>
                        </div>
                        {movie.reviews.map(review => (
                            <div className="review">
                                <img src={review.user.profilePic || 'https://wallpapers.com/images/hd/netflix-profile-pictures-1000-x-1000-88wkdmjrorckekha.jpg'} alt="" />
                                <div className="reviewText">
                                    <div className="reviewUser">
                                        <h3>{review.user.username}</h3>
                                        <span>{review.createdAt.substring(0, 10)}</span>
                                    </div>
                                    <p>{review.comment}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    )
}
