package handlers

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
)

func GenerateId() string {
	id := make([]byte, 3)
	_, err := rand.Read(id)
	if err != nil {
		return ""
	}

	return hex.EncodeToString(id)
}
func CreateRoom(w http.ResponseWriter, r *http.Request) {
	LoadRoom()
	fmt.Println("== CreateRoom called ==")

	if r.Method != http.MethodPost {
		fmt.Println("Wrong method:", r.Method)
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	room_name := r.FormValue("roomname")
	fmt.Println("Room name:", room_name)

	if room_name == "" {
		fmt.Println("Room name is empty")
		http.Error(w, "room required", http.StatusBadRequest)
		return
	}

	if len(room_name) > 15 {
		fmt.Println("Room name too long")
		http.Error(w, "name too long", http.StatusBadRequest)
		return
	}

	for _, rm := range rooms {
		if rm.Name == room_name {
			fmt.Println("Room already exists")
			http.Error(w, "room already exists", http.StatusBadRequest)
			return
		}
	}

	roomID := GenerateId()
	fmt.Println("Generated ID:", roomID)

	user, Exist := Get_home_user(r)
	if !Exist {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	room := &Rooms{
		ID:    roomID,
		Name:  room_name,
		Owner: user.Gitea,
	}

	rooms[roomID] = room
	SaveRoom()

	fmt.Println("Rooms in map:", len(rooms))
	fmt.Println("Redirecting to:", "/room?id="+roomID)

	http.Redirect(w, r, "/room?id="+roomID, http.StatusSeeOther)
}
