import { Link, useLocation } from "react-router-dom"
import "./product.css"
import { useState } from "react";
import { useContext } from "react";
import { MovieContext } from "../../context/movieContext/MovieContext";
import { updateMovie } from "../../context/movieContext/apiCalls";

export default function Product() {
    const location = useLocation();
    const [movie, setMovie] = useState(location.state.movie);
    const { dispatch } = useContext(MovieContext);

    const handleChange = (e) => {
        const value = e.target.value;
        setMovie({ ...movie, [e.target.name]: value });
    }

    const handleUpdate = (e) => {
        e.preventDefault();
        updateMovie(movie, dispatch);
    }

    return (
        <div className="product">
            <div className="productTitleContainer">
                <h1 className="productTitle">Movie</h1>
                <Link to="/newProduct">
                    <button className="productAddButton">Create</button>
                </Link>
            </div>
            <div className="productTop">
                <div className="productTopRight">
                    <div className="productInfoTop">
                        <img src={movie.img} alt="" className="productInfoImg" />
                        <span className="productName">{movie.title}</span>
                    </div>
                    <div className="productInfoBottom">
                        <div className="productInfoItem">
                            <span className="productInfoKey">id:</span>
                            <span className="productInfoValue">{movie._id}</span>
                        </div>
                        <div className="productInfoItem">
                            <span className="productInfoKey">genre:</span>
                            <span className="productInfoValue">{movie.genre}</span>
                        </div>
                        <div className="productInfoItem">
                            <span className="productInfoKey">year:</span>
                            <span className="productInfoValue">{movie.year}</span>
                        </div>
                        <div className="productInfoItem">
                            <span className="productInfoKey">limit:</span>
                            <span className="productInfoValue">{movie.limit}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div className="productBottom">
                <form className="productForm">
                    <div className="productFormLeft">
                        <label>Movie Title</label>
                        <input type="text" name="title" placeholder={movie.title} onChange={handleChange} />
                        <label>Year</label>
                        <input type="text" name="year" placeholder={movie.year} onChange={handleChange} />
                        <label>Genre</label>
                        <input type="text" name="genre" placeholder={movie.genre} onChange={handleChange} />
                        <label>Limit</label>
                        <input type="text" name="limit" placeholder={movie.limit} onChange={handleChange} />
                        <label>Trailer</label>
                        <input type="text" name="trailer" placeholder={movie.trailer} onChange={handleChange} />
                        <label>Video</label>
                        <input type="text" name="video" placeholder={movie.video} onChange={handleChange} />
                        <label>Image</label>
                        <input type="text" id="img" placeholder={movie.img} name="img" onChange={handleChange} />
                        <label>Image Title</label>
                        <input type="text" id="imgTitle" placeholder={movie.imgTitle} name="imgTitle" onChange={handleChange} />
                        <label>Image Thumbnail</label>
                        <input type="text" id="imgSm" placeholder={movie.imgSm} name="imgSm" onChange={handleChange} />
                    </div>
                    <div className="productFormRight">
                        <div className="productUpload">
                            <img src={movie.img} alt="" className="productUploadImg" />
                        </div>
                        <button className="productButton" onClick={handleUpdate}>Update</button>
                    </div>
                </form>
            </div>
        </div>
    )
}
