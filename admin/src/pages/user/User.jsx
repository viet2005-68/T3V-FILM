import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import "./user.css";
import {
    CalendarToday,
    LocationCity,
    MailOutline,
    PermIdentity,
    PhoneAndroid,
    Publish,
} from "@mui/icons-material";

export default function User() {
    const { id } = useParams();
    const [user, setUser] = useState(null);
    const [formData, setFormData] = useState({});
    const token = "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken;

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await axios.get(`/api/users/find/${id}`, {
                    headers: { token },
                });
                setUser(res.data);
                setFormData({
                    username: res.data.username || "",
                    email: res.data.email || "",
                    profilePic: res.data.profilePic || "",
                    age: res.data.age || "",
                    favoriteGenre: res.data.favoriteGenre || "",
                    gender: res.data.gender || "",
                });
            } catch (err) {
                console.error("Lỗi lấy user:", err);
            }
        };
        fetchUser();
    }, [id]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        try {
            await axios.put(`/api/users/${id}`, formData, {
                headers: { token },
            });
            alert("Cập nhật thành công!");
        } catch (err) {
            console.error("Lỗi cập nhật:", err);
            alert("Cập nhật thất bại.");
        }
    };

    if (!user) return <p>Loading...</p>;

    return (
        <div className="user">
            <div className="userTitleContainer">
                <h1 className="userTitle">Edit User</h1>
                <Link to="/newUser">
                    <button className="userAddButton">Create</button>
                </Link>
            </div>
            <div className="userContainer">
                <div className="userShow">
                    <div className="userShowTop">
                        <img
                            src={
                                formData.profilePic?.trim()
                                    ? formData.profilePic
                                    : "https://wallpapers.com/images/hd/netflix-profile-pictures-1000-x-1000-88wkdmjrorckekha.jpg"
                            }
                            alt="avatar"
                            className="userShowImg"
                        />
                        <div className="userShowTopTitle">
                            <span className="userShowUsername">{formData.username}</span>
                            <span className="userShowUserTitle">{formData.favoriteGenre || "User"}</span>
                        </div>
                    </div>
                    <div className="userShowBottom">
                        <span className="userShowTitle">User Info</span>
                        <div className="userShowInfo">
                            <PermIdentity className="userShowIcon" />
                            <span className="userShowInfoTitle">{formData.username}</span>
                        </div>
                        <div className="userShowInfo">
                            <CalendarToday className="userShowIcon" />
                            <span className="userShowInfoTitle">{formData.age}</span>
                        </div>
                        <div className="userShowInfo">
                            <MailOutline className="userShowIcon" />
                            <span className="userShowInfoTitle">{formData.email}</span>
                        </div>
                        <div className="userShowInfo">
                            <LocationCity className="userShowIcon" />
                            <span className="userShowInfoTitle">{formData.favoriteGenre}</span>
                        </div>
                    </div>
                </div>

                <div className="userUpdate">
                    <span className="userUpdateTitle">Edit</span>
                    <form className="userUpdateForm" onSubmit={handleUpdate}>
                        <div className="userUpdateLeft">
                            <div className="userUpdateItem">
                                <label>Username (Required)</label>
                                <input
                                    type="text"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    className="userUpdateInput"
                                    required
                                />
                            </div>
                            <div className="userUpdateItem">
                                <label>Email (Required)</label>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className="userUpdateInput"
                                    required
                                />
                            </div>
                            <div className="userUpdateItem">
                                <label>Profile Picture URL</label>
                                <input
                                    type="text"
                                    name="profilePic"
                                    value={formData.profilePic}
                                    onChange={handleChange}
                                    className="userUpdateInput"
                                />
                            </div>
                            <div className="userUpdateItem">
                                <label>Age</label>
                                <input
                                    type="number"
                                    name="age"
                                    value={formData.age}
                                    onChange={handleChange}
                                    className="userUpdateInput"
                                />
                            </div>
                            <div className="userUpdateItem">
                                <label>Favorite Genre</label>
                                <input
                                    type="text"
                                    name="favoriteGenre"
                                    value={formData.favoriteGenre}
                                    onChange={handleChange}
                                    className="userUpdateInput"
                                />
                            </div>
                            <div className="userUpdateItem">
                                <label>Gender</label>
                                <div>
                                    <label>
                                        <input
                                            type="radio"
                                            name="gender"
                                            value="Male"
                                            checked={formData.gender === "Male"}
                                            onChange={handleChange}
                                        />
                                        Male
                                    </label>
                                    <label style={{ marginLeft: "20px" }}>
                                        <input
                                            type="radio"
                                            name="gender"
                                            value="Female"
                                            checked={formData.gender === "Female"}
                                            onChange={handleChange}
                                        />
                                        Female
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div className="userUpdateRight">
                            <div className="userUpdateUpload">
                                <img
                                    src={
                                        formData.profilePic?.trim()
                                            ? formData.profilePic
                                            : "https://wallpapers.com/images/hd/netflix-profile-pictures-1000-x-1000-88wkdmjrorckekha.jpg"
                                    }
                                    className="userUpdateImg"
                                    alt="avatar"
                                />
                                <label htmlFor="file">
                                    <Publish className="userUpdateIcon" />
                                </label>
                                <input type="file" style={{ display: "none" }} id="file" />
                            </div>
                            <button type="submit" className="userUpdateButton">
                                Update
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
