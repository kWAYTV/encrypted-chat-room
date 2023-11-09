import sys, socket, threading
from tkinter import *
from kwslogger import Logger
from tkinter import messagebox
from Crypto.Cipher import ChaCha20
from matplotlib.colors import to_hex
from matplotlib.colors import is_color_like

# Initialize the logger
logger = Logger()

logger.create_logo("EC Client")

PORT = 8000
SERVER = "127.0.0.1"
ADDRESS = (SERVER, PORT)
chakey = b'12345678901234567890123465790123'  # key should be 32 bytes

# Create a new client socket
# and connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# GUI class for the chat
class GUI:
    def __init__(self):

        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()

        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.Window.destroy()
                client.close()

        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=400, height=300)
        # create a Label
        self.pls = Label(self.login, text="Please login to continue", justify=CENTER, font="BookAntiqua 12")

        self.pls.place(relheight=0.15, relx=0.2, rely=0.07)
        # create a Label
        self.labelName = Label(self.login, text="Name: ", font="BookAntiqua 12")

        self.labelName.place(relheight=0.2, relx=0.1, rely=0.2)

        # create a entry box for
        # typing the message
        self.entryName = Entry(self.login, font="BookAntiqua 12")
        self.entryName.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.2)

        self.labelRoomName = Label(self.login, text="Room: ", font="BookAntiqua 12")

        self.labelRoomName.place(relheight=0.2, relx=0.1, rely=0.4)

        self.roomName = Entry(self.login, font="BookAntiqua 12")
        self.roomName.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.4)

        self.labelRoomColor = Label(self.login, text="Room color: ", font="BookAntiqua 12")

        self.labelRoomColor.place(relheight=0.2, relx=0.1, rely=0.6)

        self.roomColor = Entry(self.login, font="BookAntiqua 12")
        self.roomColor.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.6)

        # set the focus of the cursor
        self.entryName.focus()

        # create a Continue Button
        # along with action
        self.go = Button(self.login, text="Continue", font="BookAntiqua 12", command=lambda: self.go_ahead(self.entryName.get( ), self.roomName.get(), self.roomColor.get()))

        self.go.place(relx=0.4, rely=0.8)
        self.Window.protocol("WM_DELETE_WINDOW", on_closing)
        self.login.protocol("WM_DELETE_WINDOW", on_closing)
        self.Window.mainloop()

    def go_ahead(self, name, room, color):
        self.login.destroy()
        logger.success('Access granted!')
        room = room.upper()

        if not name or not room:
            logger.error('Room name is missing')
            messagebox.showerror("showerror", "Invalid Name/Room entered.")
            sys.exit(1)

        if not is_color_like(color):
            logger.error('Room color is not valid')
            messagebox.showerror("showerror", "Invalid Room color entered.")
            sys.exit(1)

        if to_hex(color) == '#000000':
            messagebox.showwarning("Warning", "Black is not an acceptable Room color.\nRoom color set to White.")
            color = "White"

        self.layout(name, room, color)

        try:
            client.connect(ADDRESS)
        except ConnectionRefusedError as e:
            messagebox.showerror("Connection Error", f"Unable to connect to server: {e}")
            sys.exit(1)

        client.send(room.encode())
        response = client.recv(10)
        if response != b'ok':
            logger.error('Could not connect (does room exist?)')
            messagebox.showwarning("Warning", "The Room you entered does not exist.")
            sys.exit(1)

        client.send(name.encode())
        client.recv(10)
        joined = (f"[{name}] HAS JOINED THE CHAT!").encode()
        left = (f"[{name}] HAS LEFT THE CHAT!").encode()

        # chacha20 encryption
        cipher = ChaCha20.new(key=chakey)
        ciphertext = cipher.encrypt(joined)
        client.send(cipher.nonce + ciphertext)
        client.recv(10)

        cipher2 = ChaCha20.new(key=chakey)
        ciphertext2 = cipher2.encrypt(left)
        client.send(cipher2.nonce + ciphertext2)
        client.recv(10)

        # the thread to receive messages
        rcv = threading.Thread(target=self.receive)
        rcv.start()

    # The main layout of the chat
    def layout(self, name, room, color):

        self.name = name
        self.room = room
        self.color = color
        # to show chat window
        self.Window.deiconify()
        self.Window.title("Chatroom")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=470, height=550, bg='Black')
        self.labelHead = Label(self.Window, bg="gray38", fg="snow", text=self.room, font="BookAntiqua 12", pady=5)

        self.labelHead.place(relwidth=1)
        self.line = Label(self.Window, width=450, bg="#ABB2B9")

        self.line.place(relwidth=1, rely=0.07, relheight=0.012)

        self.textCons = Text(self.Window, width=20, height=2, bg=self.color, fg="gray1", font="BookAntiqua 12", padx=5, pady=5)

        self.textCons.place(relheight=0.745, relwidth=1, rely=0.08)

        self.labelBottom = Label(self.Window, bg="#ABB2B9", height=80)

        self.labelBottom.place(relwidth=1, rely=0.825)

        self.entryMsg = Entry(self.labelBottom, bg='snow', fg='gray1', font="BookAntiqua 12")

        # place the given widget into the gui window
        self.entryMsg.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)

        self.entryMsg.focus()

        # create a Send Button
        self.buttonMsg = Button(self.labelBottom, text="Send", font="Helvetica 10 bold", width=20, bg="#ABB2B9", command=lambda: self.send_button(self.entryMsg.get()))

        self.buttonMsg.place(relx=0.77,  rely=0.008, relheight=0.06, relwidth=0.22)

        self.textCons.config(cursor="arrow")

        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)

        # place the scroll bar into the gui window
        scrollbar.place(relheight=1, relx=0.974)

        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=DISABLED)

    # function to basically start the thread for sending messages
    def send_button(self, msg):
        self.textCons.config(state=DISABLED)
        self.msg = msg
        self.entryMsg.delete(0, END)
        snd = threading.Thread(target=self.send_message)
        snd.start()

    # function to receive messages
    def receive(self):
        logger.info('Listening started.')
        while True:
            try:
                data = client.recv(4096)

                #encryption_len = 16  # for aes
                encryption_len = 8  # for chacha20

                # if there is at least 1 byte encrypted
                if data and len(data) > encryption_len + 1:

                    # chacha20 decryption
                    nonce = data[:encryption_len]  # 8 bytes for the nonce
                    ciphertext = data[
                        encryption_len:]  # the rest of the data is encrypted
                    cipher = ChaCha20.new(key=chakey, nonce=nonce)
                    message = cipher.decrypt(ciphertext)
                    message = message.decode(errors="ignore")
                    logger.info(f"Received message: {message}")

                    # insert messages to text box
                    self.textCons.config(state=NORMAL)
                    self.textCons.insert(END, message + "\n\n")

                    self.textCons.config(state=DISABLED)
                    self.textCons.see(END)
            except socket.error:
                #logger.error('Connection error')
                client.close()
                break
            except:
                # an error will be printed on the command line or console if there's an error
                logger.error("An error occurred!")
                # continue

    # function to send messages
    def send_message(self):
        self.textCons.config(state=DISABLED)

        message = (f"{self.name}: {self.msg}").encode()

        try:
            # chacha20 encryption
            cipher = ChaCha20.new(key=chakey)
            ciphertext = cipher.encrypt(message)
            client.send(cipher.nonce + ciphertext)
        except BrokenPipeError:
            logger.error('Server is down')
            self.Window.destroy()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.Window.destroy()

# create a GUI class object
g = GUI()