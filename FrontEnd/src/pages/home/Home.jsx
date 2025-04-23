import { useEffect, useState } from "react";
import axios from "axios";

import Featured from "../../components/featured/Featured.jsx";
import List from "../../components/list/List.jsx";
import TrendingList from "../../components/Trending/TrendingList.jsx";
import FilmSpecialList from "../../components/filmSpeacialList/filmSpeacialList.jsx";

import "./home.scss";

export default function Home({ type }) {
    const [lists, setLists] = useState([]);
    const [genre, setGenre] = useState(null);
    const [allMovie, setAllMovie] = useState([]);
    const [topMovie, setTopMovie] = useState([]);
    const [recommendedMovie, setRecommendedMovie] = useState([])

    const getRecommended = async () => {
        try {
            const res = await axios.get(`/recommender/${JSON.parse(localStorage.getItem("user"))._id}`);
            const movieArr = await Promise.all(
                Object.keys(res.data.data).map(async (key) => {
                    const subRes = await axios.get(`/api/movies/${key}`, {
                        headers: {
                            token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                        },
                    });
                    return subRes.data;
                })
            );
            return movieArr;
        } catch (err) {
            console.log(err);
        }
    };

    useEffect(() => {
        const fetchRecommed = async () => {
            const recommended = await getRecommended()
            setRecommendedMovie(recommended)
        }

        fetchRecommed()
    }, [])

    useEffect(() => {
        const getRandomLists = async () => {
            try {
                const res = await axios.get(
                    `/api/lists${type ? "?type=" + type : ""}${genre ? "&genre=" + genre : ""
                    }`,
                    {
                        headers: {
                            token:
                                "Bearer " +
                                JSON.parse(localStorage.getItem("user")).accessToken,
                        },
                    }
                );
                setLists(res.data);
            } catch (err) {
                console.log(err);
            }
        };

        const getAllMovie = async () => {
            try {
                if (genre) {
                    const res = await axios.get(`/api/movies?genre=${genre}`, {
                        headers: {
                            token:
                                "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                        },
                    });
                    setAllMovie(res.data);
                }
                else {
                    const res = await axios.get("/api/movies?limit=10", {
                        headers: {
                            token:
                                "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                        },
                    });
                    setAllMovie(res.data);
                }
            } catch (err) {
                console.log(err);
            }
        };

        const getTopMovies = async () => {
            try {
                const res = await axios.get("/api/movies/top", {
                    headers: {
                        token:
                            "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setTopMovie(res.data);
            } catch (err) {
                console.log(err);
            }
        };

        getRandomLists();
        getAllMovie();
        getTopMovies();
    }, [type, genre]);

    const sampleFilms = [
        {
            id: 1,
            title: "Khi cuộc đời...",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
        },
        {
            id: 2,
            title: "One Piece",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
        },
        {
            id: 3,
            title: "404 Chạy ngay đi",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
        },
        {
            id: 4,
            title: "Nghiệp duyên",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
        },
    ];

    const specialFilms = [
        {
            id: 101,
            title: "Mai",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2022",
            limit: "15+",
        },
        {
            id: 102,
            title: "Gương đen",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2021",
            limit: "16+",
        },
        {
            id: 103,
            title: "Nghiệp duyên",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2020",
            limit: "18",
        },
        {
            id: 104,
            title: "Khi cuộc đời...",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2023",
            limit: "13",
        },
        {
            id: 104,
            title: "Khi cuộc đời...",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2023",
            limit: "13",
        },
        {
            id: 104,
            title: "Khi cuộc đời...",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2023",
            limit: "13",
        },
        {
            id: 104,
            title: "Khi cuộc đời...",
            img: "https://th.bing.com/th/id/R.0345c19ae9c7a64955356809ce9d2b5f?rik=GZuDpMCkomqIGw&pid=ImgRaw&r=0",
            year: "2023",
            limit: "13",
        },
    ];

    return (
        <div className="home">
            <Featured type={type} setGenre={setGenre} />
            <List
                list={{
                    title: "All Movies",
                    content: allMovie.map((movie) => movie._id),
                }}
            />
            {lists.map((list) => (
                <List key={list._id} list={list} />
            ))}
            <TrendingList films={topMovie} title={"Most Popular"} />
            <TrendingList films={recommendedMovie ?? []} title={"Recommended For You"} />
            <FilmSpecialList movies={allMovie} />
        </div>
    );
}
