<script setup>
import { ref, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { meetingService } from '../services/api'
import moment from 'moment'

const meetings = ref([])
const loading = ref(true)
const showNewMeetingModal = ref(false)
const editingMeeting = ref(null)

const newMeeting = ref({
  title: '',
  description: '',
  location: '',
  start_time: '',
  end_time: ''
})

onMounted(async () => {
  await fetchMeetings()
})

const fetchMeetings = async () => {
  try {
    loading.value = true
    const response = await meetingService.getMeetings()
    meetings.value = response.data
  } catch (error) {
    console.error('Error fetching meetings:', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    if (editingMeeting.value) {
      await meetingService.updateMeeting(editingMeeting.value.id, newMeeting.value)
    } else {
      await meetingService.createMeeting(newMeeting.value)
    }
    await fetchMeetings()
    closeModal()
  } catch (error) {
    console.error('Error saving meeting:', error)
  }
}

const startEdit = (meeting) => {
  editingMeeting.value = meeting
  newMeeting.value = {
    title: meeting.title,
    description: meeting.description || '',
    location: meeting.location || '',
    start_time: meeting.start_time ? moment(meeting.start_time).format('YYYY-MM-DDTHH:mm') : '',
    end_time: meeting.end_time ? moment(meeting.end_time).format('YYYY-MM-DDTHH:mm') : ''
  }
  showNewMeetingModal.value = true
}

const deleteMeeting = async (id) => {
  if (confirm('Are you sure you want to delete this meeting?')) {
    try {
      await meetingService.deleteMeeting(id)
      await fetchMeetings()
    } catch (error) {
      console.error('Error deleting meeting:', error)
    }
  }
}

const closeModal = () => {
  showNewMeetingModal.value = false
  editingMeeting.value = null
  newMeeting.value = {
    title: '',
    description: '',
    location: '',
    start_time: '',
    end_time: ''
  }
}

const formatDateTime = (date) => {
  return moment(date).format('MMM D, YYYY h:mm A')
}
</script>

<template>  <Layout>
    <div class="h-full space-y-6">
      <!-- Header Section -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Meetings</h1>
            <p class="mt-2 text-gray-600">Schedule and manage your meetings</p>
          </div>
          <button
            @click="showNewMeetingModal = true"
            class="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-6 py-3 text-base font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-150"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Schedule Meeting
          </button>
        </div>

        <!-- Quick Filters -->
        <div class="mt-6 flex flex-wrap gap-4">
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            All Meetings
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Today
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            This Week
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Upcoming
          </button>
        </div>
      </div>

      <!-- Meetings Calendar/List View Toggle -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-4">
            <button class="text-blue-600 font-medium">List View</button>
            <button class="text-gray-500 hover:text-gray-700">Calendar View</button>
          </div>
          <div class="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Search meetings..."
              class="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- Meetings List -->
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="meetings.length === 0" class="flex flex-col items-center justify-center h-64">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 class="text-lg font-medium text-gray-900">No meetings scheduled</h3>
          <p class="mt-1 text-gray-500">Schedule your first meeting to get started!</p>
          <button
            @click="showNewMeetingModal = true"
            class="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Schedule Meeting
          </button>
        </div>

        <div v-else class="overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-300">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="py-4 pl-6 pr-3 text-left text-sm font-semibold text-gray-900">Meeting Details</th>
                  <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Participants</th>
                  <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Time & Location</th>
                  <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th scope="col" class="relative py-4 pl-3 pr-6">
                    <span class="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr v-for="meeting in meetings" :key="meeting.id" class="hover:bg-gray-50 transition-colors duration-150">
                  <td class="py-4 pl-6 pr-3">
                    <div class="flex items-start space-x-3">
                      <div class="flex-shrink-0">
                        <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                          <span class="text-blue-600 text-lg font-medium">
                            {{ meeting.title.charAt(0).toUpperCase() }}
                          </span>
                        </div>
                      </div>
                      <div>
                        <div class="text-sm font-medium text-gray-900">{{ meeting.title }}</div>
                        <div class="text-sm text-gray-500 mt-1">{{ meeting.description || 'No description' }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-4">
                    <div class="flex -space-x-2">
                      <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center border-2 border-white">
                        <span class="text-xs font-medium text-gray-600">You</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-4">
                    <div>
                      <div class="text-sm text-gray-900">
                        {{ formatDateTime(meeting.start_time) }}
                      </div>
                      <div class="text-sm text-gray-500">
                        to {{ formatDateTime(meeting.end_time) }}
                      </div>
                      <div v-if="meeting.location" class="text-sm text-gray-500 mt-1 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {{ meeting.location }}
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-4">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Confirmed
                    </span>
                  </td>
                  <td class="relative py-4 pl-3 pr-6 text-right">
                    <div class="flex items-center justify-end space-x-3">
                      <button
                        @click="startEdit(meeting)"
                        class="text-blue-600 hover:text-blue-900 flex items-center"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Edit
                      </button>
                      <button
                        @click="deleteMeeting(meeting.id)"
                        class="text-red-600 hover:text-red-900 flex items-center"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Meeting Modal -->
    <div v-if="showNewMeetingModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg max-w-lg w-full p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">
          {{ editingMeeting ? 'Edit Meeting' : 'Schedule Meeting' }}
        </h3>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Title</label>
            <input
              type="text"
              v-model="newMeeting.title"
              required
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              v-model="newMeeting.description"
              rows="3"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              v-model="newMeeting.location"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Start Time</label>
            <input
              type="datetime-local"
              v-model="newMeeting.start_time"
              required
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">End Time</label>
            <input
              type="datetime-local"
              v-model="newMeeting.end_time"
              required
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3">
            <button
              type="submit"
              class="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:text-sm"
            >
              {{ editingMeeting ? 'Save Changes' : 'Schedule Meeting' }}
            </button>
            <button
              type="button"
              @click="closeModal"
              class="mt-3 inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:mt-0 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </Layout>
</template>
