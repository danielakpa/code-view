package handlers

type Message struct {
	Users string
	Text  string
}

type Comments struct {
	User string
	Text string
}

type Rooms struct {
	ID         string
	Name       string
	Owner      string
	RoomCode   string
	CodeOwner  string
	CodeLocked bool
	Messages   []Message
	Comments   []Comments
}

var sessions = make(map[string]User)

var rooms = make(map[string]*Rooms)
