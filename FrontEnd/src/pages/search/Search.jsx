import Navbar from "../../components/navbar/Navbar.jsx";
import List from "../../components/List/List.jsx";
import Filter from "../../components/Filter/Filter.jsx";
import SearchCard from "../../components/SearchCard/SearchCard.jsx";
import {MdManageSearch} from "react-icons/md";
import {TablePagination, Box} from "@mui/material";
import {useEffect, useState} from "react";
import axios from "axios";
import "./search.scss"

function Header({query}) {
    return (
        <div className="row-header">
            <div className="icon">
                <MdManageSearch size={40} color="white"/>
            </div>
            <h3 className="category-name">
                Kết quả tìm kiếm "{query || "Tất cả"}"
            </h3>
        </div>
    );
}

function Tab({ selectedTab, onTabChange }) {
    return (
        <div className="row-tabs-container">
            <a
                className={selectedTab === "movies" ? "active" : ""}
                onClick={() => onTabChange("movies")}
            >
                Phim
            </a>
            <a
                className={selectedTab === "actors" ? "active" : ""}
                onClick={() => onTabChange("actors")}
            >
                Diễn viên
            </a>
        </div>
    );
}



export default function Search({type}) {
    const [query, setQuery] = useState("");
    const [lists, setLists] = useState([]);
    const [genre, setGenre] = useState(null);
    const [allMovie, setAllMovie] = useState([]);
    const [searchMovies, setSearchMovies] = useState([]);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);

    const moviesPerPage = 8;
    useEffect(() => {
        const getSearchMovies = async () => {
            try {
                const response = await axios.get(`/api/movies?title=${query}`, {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setSearchMovies(response.data);
            } catch (error) {
                console.error(error);
            }
        };

        if (query.trim() !== "") {
            getSearchMovies();
        } else {
            setSearchMovies(allMovie); // fallback: hiển thị toàn bộ khi không có từ khóa
        }
    }, [query, allMovie]);

    useEffect(() => {
        const getSearchMovies = async () => {
            try {
                const response = await axios.get(`/api/movies?title=${query}` , {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setSearchMovies(response.data);
            } catch (error) {
                console.error(error);
            }
        }
        const getRandomLists = async () => {
            try {
                const res = await axios.get(`/api/lists${type ? "?type=" + type : ""}${genre ? "&genre=" + genre : ""}`, {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setLists(res.data);
            } catch (err) {
                console.log(err);
            }
        };

        const getAllMovie = async () => {
            try {
                const res = await axios.get("/api/movies", {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                console.log(res.data);
                setAllMovie(res.data);
            } catch (err) {
                console.log(err);
            }
        };

        getRandomLists();
        getAllMovie();
    }, [type, genre]);
    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };
    return (<div className="search">
        <Navbar/>
        <div className="search-content">
            <Header query={query}/>
           <div className="tab-content">
                <Filter/>
               {searchMovies.length === 0 && (
                   <p style={{ color: "#fff", marginTop: "1rem" }}>Không tìm thấy phim {query} nào.</p>
               )}
               <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "repeat(1, 1fr)",    // điện thoại: 1 cột
                            sm: "repeat(2, 1fr)",    // tablet nhỏ: 2 cột
                            md: "repeat(3, 1fr)",    // tablet lớn: 3 cột
                            lg: "repeat(4, 1fr)",    // desktop: 4 cột
                            xl: "repeat(5, 1fr)",    // màn lớn: 5 cột
                        },
                        rowGap: 0,
                    }}
                >
                    {searchMovies
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map((movie, index) => (
                            <Box key={movie._id} sx={{ overflow: "visible" }}>
                                <SearchCard key={movie.id} movieId={movie._id} index={index} />
                            </Box>
                        ))}
                </Box>
                <TablePagination className="pagination"
                                 component="div"
                                 count={searchMovies.length}
                                 page={page}
                                 onPageChange={handleChangePage}
                                 rowsPerPage={rowsPerPage}
                                 onRowsPerPageChange={handleChangeRowsPerPage}
                                 sx={{
                                     color: "white",            // Màu chữ chính
                                     '.MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows': {
                                         color: 'white',          // Label và số trang
                                     }, '.MuiSvgIcon-root': {
                                         color: 'white',          // Icon mũi tên
                                     },
                                 }}
                />
            </div>
        </div>
    </div>);
}