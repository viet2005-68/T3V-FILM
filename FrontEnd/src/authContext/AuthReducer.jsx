const AuthReducer = (state, action) => {
  switch (action.type) {
    case "LOGIN_START":
      return {
        user: null,
        isEmailVerified: true,
        isFetching: true,
        error: false,
      };
    case "LOGIN_SUCCESS":
      return {
        user: action.payload,
        isEmailVerified: true,
        isFetching: false,
        error: false,
      };
    case "LOGIN_FAILURE":
      return {
        user: null,
        isFetching: false,
        error: true,
      };
    case "LOGOUT":
      return {
        user: null,
        isEmailVerified: false,
        isFetching: false,
        error: false,
      };
    case "VERIFY_EMAIL_START":
      return {
        ...state,
        isFetching: true,
        error: false,
      };
    case "VERIFY_EMAIL_SUCCESS":
      return {
        user: action.payload, // Thêm thông tin user nếu có
        isEmailVerified: true, // Đặt lại isAuthenticated thành true
        isFetching: false,
        error: false,
      };
    case "VERIFY_EMAIL_FAILURE":
      return {
        ...state,
        isFetching: false,
        error: true,
      };

    case "FORGET_EMAIL_FAILURE":
      return {
        ...state,
        isFetching: false,
        error: true,
      };

    case "FORGET_EMAIL_SUCCESS":
      return {
        user: action.payload,
        isEmailVerified: true,
        isFetching: false,
        error: false,
      };

    case "FORGET_EMAIL_START":
      return {
        ...state,
        isFetching: true,
        error: false,
      };

    case "RESET_EMAIL_START":
      return {
        ...state,
        isFetching: true,
        error: false,
      };

      case "RESET_EMAIL_FAILURE":
        return {
          ...state,
          isFetching: false,
          error: true,
        };

        case "RESET_EMAIL_SUCCESS":
          return {
            user: action.payload,
            isEmailVerified: true,
            isFetching: false,
            error: false,
          };
    default:
      return {
        ...state,
      };
  }
};

export default AuthReducer;
