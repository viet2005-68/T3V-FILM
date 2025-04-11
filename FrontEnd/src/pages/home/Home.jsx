import { useEffect, useState } from "react";
import axios from "axios";

import Featured from "../../components/featured/Featured.jsx";
import List from "../../components/list/List.jsx";
import Navbar from "../../components/navbar/Navbar.jsx";
import TrendingList from "../../components/Trending/TrendingList.jsx";
import FilmSpecialList from "../../components/filmSpeacialList/filmSpeacialList.jsx";

import "./home.scss";

export default function Home({ type }) {
  const [lists, setLists] = useState([]);
  const [genre, setGenre] = useState(null);
  const [allMovie, setAllMovie] = useState([]);

  useEffect(() => {
    const getRandomLists = async () => {
      try {
        const res = await axios.get(
          `/api/lists${type ? "?type=" + type : ""}${
            genre ? "&genre=" + genre : ""
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
        const res = await axios.get("/api/movies", {
          headers: {
            token:
              "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
          },
        });
        setAllMovie(res.data);
      } catch (err) {
        console.log(err);
      }
    };

    getRandomLists();
    getAllMovie();
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
  ];

  return (
    <div className="home">
      <Navbar />
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
      <TrendingList films={sampleFilms} />
      <TrendingList films={sampleFilms} />
      <FilmSpecialList movies={specialFilms} />
    </div>
  );
}
