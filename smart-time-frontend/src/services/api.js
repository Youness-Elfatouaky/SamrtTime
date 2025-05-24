import axios from 'axios'

const apiClient = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json'
    }
})

apiClient.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

export const authService = {
    login: async (credentials) => {
        const formData = new URLSearchParams()
        formData.append('username', credentials.login)
        formData.append('password', credentials.password)
        const response = await apiClient.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
        return response.data
    },
    register: (userData) => apiClient.post('/auth/register', userData),
    getProfile: () => apiClient.get('/users/me')
}

export const taskService = {
    getTasks: () => apiClient.get('/tasks'),
    createTask: (task) => apiClient.post('/tasks', task),
    updateTask: (id, task) => apiClient.put(`/tasks/${id}`, task),
    deleteTask: (id) => apiClient.delete(`/tasks/${id}`)
}

export const meetingService = {
    getMeetings: () => apiClient.get('/meetings'),
    createMeeting: (meeting) => apiClient.post('/meetings', meeting),
    updateMeeting: (id, meeting) => apiClient.put(`/meetings/${id}`, meeting),
    deleteMeeting: (id) => apiClient.delete(`/meetings/${id}`)
}

export const chatService = {
    sendMessage: (message) => apiClient.post('/agent/chat', { message })
}

export default apiClient
