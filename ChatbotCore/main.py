from graph import execute_with_langgraph
from config import chat_history

def main():
    """Main function to run the chatbot from the command line."""
    print("T3V Chatbot - Demo 8")
    print("Nhập 'exit' hoặc 'quit' để thoát")
    print("Nhập 'reset' hoặc 'clear' để xóa lịch sử chat")
    
    # Lịch sử chat được giữ ở cấp toàn cục để duy trì giữa các lần gọi
    global chat_history
    
    while True:
        try:
            query = input("\n👤 Bạn: ")
            if query.strip().lower() in ["exit", "quit", "thoát"]:
                print("Tạm biệt!")
                break
            
            if query.strip().lower() in ["reset", "clear", "xóa"]:
                chat_history = []
                print("Đã xóa lịch sử chat.")
                continue
                
            # Gọi hàm xử lý với lịch sử chat
            response = execute_with_langgraph(query)
            print(f"\nT3V: {response}")
            
        except KeyboardInterrupt:
            print("\nTạm biệt!")
            break
        except Exception as e:
            print(f"\n Lỗi: {e}")

if __name__ == "__main__":
    main() 