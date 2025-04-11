import { InfoOutlined, PlayArrow } from "@mui/icons-material"
import "./featured.scss"
import { useState, useEffect } from "react";
import axios from "axios";

export default function Featured({ type, setGenre }) {
    const [content, setContent] = useState({});

    useEffect(() => {
        const getRandomContent = async () => {
            try {
                const res = await axios.get(`/api/movies/random?type=${type}`, {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken
                    }
                });
                setContent(res.data[0]);
            }
            catch (err) {
                console.log(err);
            }
        };

        getRandomContent();
    }, [type]);
    console.log(content)
    return (
        <div className="featured">
            {type && (
                <div className="category">
                    <span>{type === 'movie' ? "Movies" : "Series"}</span>
                    <select name="genre" id="genre" onChange={e => setGenre(e.target.value)}>
                        <option >Genre</option>
                        <option value="action">Action</option>
                        <option value="adventure">Adventure</option>
                        <option value="comedy">Comedy</option>
                        <option value="crime">Crime</option>
                        <option value="fantasy">Fantasy</option>
                        <option value="historical">Historical</option>
                        <option value="horro">Horror</option>
                        <option value="romance">Romance</option>
                        <option value="sci-fi">Sci-fi</option>
                        <option value="thriller">Thriller</option>
                        <option value="western">Western</option>
                        <option value="animation">Animation</option>
                        <option value="drama">Drama</option>
                        <option value="documentary">Documentary</option>
                    </select>
                </div>
            )}
            <img src={content.img} />
            <div className="info">
                <img src={content.imgTitle} />
                <span className="desc">{content.desc}</span>
                <div className="buttons">
                    <button className="play">
                        <PlayArrow />
                        <span>Play</span>
                    </button>
                    <button className="more">
                        <InfoOutlined />
                        <span>Info</span>
                    </button>
                </div>
            </div>
        </div>
    )
}