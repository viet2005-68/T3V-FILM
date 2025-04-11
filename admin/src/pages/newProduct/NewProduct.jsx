import { useState } from "react"
import "./newProduct.css"
import { createMovie } from "../../context/movieContext/apiCalls";
import { useContext } from "react";
import { MovieContext } from "../../context/movieContext/MovieContext";
import { useNavigate } from "react-router-dom"

export default function NewProduct() {
    const [movie, setMovie] = useState({});
    const { dispatch } = useContext(MovieContext);
    const navigate = useNavigate();

    const handleChange = (e) => {
        const value = e.target.value;
        setMovie({ ...movie, [e.target.name]: value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        createMovie(movie, dispatch);
        navigate("/movies");
    }

    return (
        <div className="newProduct">
            <h1 className="addProductTitle">New Movie</h1>
            <form className="addProductForm">
                <div className="addProductItem">
                    <label>Image</label>
                    <input type="text" id="img" placeholder="image link" name="img" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Title image</label>
                    <input type="text" id="imgTitle" placeholder="image link" name="imgTitle" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Thumbnail image</label>
                    <input type="text" id="imgSm" placeholder="image link" name="imgSm" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Title</label>
                    <input type="text" placeholder="title" name="title" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Description</label>
                    <input type="text" placeholder="description" name="desc" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Year</label>
                    <input type="text" placeholder="year" name="year" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Genre</label>
                    <input type="text" placeholder="genre" name="genre" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Duration</label>
                    <input type="text" placeholder="duration" name="duration" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Limit</label>
                    <input type="text" placeholder="limit" name="limit" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Is Series?</label>
                    <select name="isSeries" id="isSeries" onChange={handleChange}>
                        <option value={false}>No</option>
                        <option value={true}>Yes</option>
                    </select>
                </div>
                <div className="addProductItem" >
                    <label>Trailer</label>
                    <input type="text" name="trailer" placeholder="embedding link" onChange={handleChange} />
                </div>
                <div className="addProductItem">
                    <label>Video</label>
                    <input type="text" name="video" placeholder="embedding link" onChange={handleChange} />
                </div>
                <button className="addProductButton" onClick={handleSubmit}>Create</button>
            </form>
        </div>
    )
}
