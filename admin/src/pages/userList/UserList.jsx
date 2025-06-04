import "./userList.css";
import { DataGrid } from "@mui/x-data-grid";
import { DeleteOutline } from "@mui/icons-material";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";

export default function UserList() {
    const [data, setData] = useState([]);
    const token = "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken; // lấy token nếu bạn đã login

    useEffect(() => {
        const getUsers = async () => {
            try {
                const res = await axios.get("/api/users", {
                    headers: { token },
                });
                // Nếu bạn muốn ẩn admin, lọc ở đây:
                // const users = res.data.filter((user) => !user.isAdmin);
                setData(res.data);
            } catch (err) {
                console.error("Lỗi khi lấy danh sách người dùng:", err);
            }
        };
        getUsers();
    }, []);

    const handleDelete = async (id) => {
        if (window.confirm("Bạn có chắc muốn xoá người dùng này?")) {
            try {
                await axios.delete(`/api/users/${id}`, {
                    headers: { token },
                });
                setData(data.filter((item) => item._id !== id));
            } catch (err) {
                alert("Không thể xoá người dùng.");
            }
        }
    };

    const columns = [
        { field: "_id", headerName: "ID", width: 200 },
        {
            field: "username",
            headerName: "Username",
            width: 150,
            renderCell: (params) => {
                return (
                    <div className="userListUser">
                        <img
                            className="userListImg"
                            src={
                                params.row.img ||
                                "https://crowd-literature.eu/wp-content/uploads/2015/01/no-avatar.gif"
                            }
                            alt=""
                        />
                        {params.row.username}
                    </div>
                );
            },
        },
        { field: "email", headerName: "Email", width: 180 },
        {
            field: "isAdmin",
            headerName: "Role",
            width: 100,
            renderCell: (params) => (
                <span>{params.row.isAdmin ? "Admin" : "User"}</span>
            ),
        },
        {
            field: "action",
            headerName: "Action",
            width: 150,
            renderCell: (params) => {
                return (
                    <>
                        <Link to={`/user/${params.row._id}`}>
                            <button className="userListEdit">Edit</button>
                        </Link>
                        <DeleteOutline
                            onClick={() => handleDelete(params.row._id)}
                            className="userListDelete"
                        />
                    </>
                );
            },
        },
    ];

    return (
        <div className="userList">
            <DataGrid
                rows={data}
                getRowId={(row) => row._id}
                disableRowSelectionOnClick
                columns={columns}
                pageSize={8}
                checkboxSelection
            />
        </div>
    );
}
