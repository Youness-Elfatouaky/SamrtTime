<script setup>
import { ref, onMounted, computed } from 'vue'
import Layout from '../components/Layout.vue'
import { meetingService } from '../services/api'
import moment from 'moment'

const meetings = ref([])
const loading = ref(true)
const showNewMeetingModal = ref(false)
const editingMeeting = ref(null)
const showDeleteConfirm = ref(false)
const meetingToDelete = ref(null)

const newMeeting = ref({
  title: '',
  description: '',
  location: '',
  start_time: '',
  end_time: ''
})

const searchQuery = ref('')
const viewMode = ref('list') // 'list', 'grid', 'calendar'
const sortBy = ref('date') // 'date', 'title'
const sortOrder = ref('asc') // 'asc', 'desc'
const selectedFilter = ref('all') // 'all', 'today', 'week', 'high-priority'

const currentWeek = ref(moment())

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

const confirmDelete = (meeting) => {
  meetingToDelete.value = meeting
  showDeleteConfirm.value = true
}

const deleteMeeting = async () => {
  try {
    await meetingService.deleteMeeting(meetingToDelete.value.id)
    await fetchMeetings()
    showDeleteConfirm.value = false
    meetingToDelete.value = null
  } catch (error) {
    console.error('Error deleting meeting:', error)
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

const formatTime = (date) => {
  return moment(date).format('HH:mm')
}

const isToday = (date) => {
  return moment().isSame(moment(date), 'day')
}

const getMeetingsInTimeSlot = (day, hour) => {
  return filteredMeetings.value.filter(meeting => {
    if (!meeting.start_time || !meeting.end_time) return false
    const meetingDate = moment(meeting.start_time)
    return meetingDate.isSame(moment(day), 'day') &&
           meetingDate.hour() <= hour &&
           moment(meeting.end_time).hour() >= hour
  })
}

const getMeetingPosition = (meeting) => {
  const start = moment(meeting.start_time)
  const end = moment(meeting.end_time)
  
  // Calculate position based on 48px per hour (h-12 = 3rem = 48px)
  const startMinutes = start.hour() * 60 + start.minute()
  const duration = moment.duration(end.diff(start)).asMinutes()
  
  const hourHeight = 67.8 // matches the h-12 class (3rem = 48px)
  const top = (startMinutes / 60) * hourHeight
  const height = (duration / 60) * hourHeight
  
  return {
    top: `${top}px`,
    height: `${Math.max(height, 34)}px`, // minimum height of 24px for very short meetings
    zIndex: 2
  }
}

const filteredMeetings = computed(() => {
  let filtered = [...meetings.value]
  
  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(meeting => 
      meeting.title.toLowerCase().includes(query) || 
      meeting.description?.toLowerCase().includes(query)
    )
  }

  // Apply category filter
  if (selectedFilter.value !== 'all') {
    const today = moment().startOf('day')
    const endOfToday = moment().endOf('day')
    const endOfWeek = moment().endOf('week')

    filtered = filtered.filter(meeting => {
      const meetingDate = moment(meeting.start_time)
      switch (selectedFilter.value) {
        case 'today':
          return meetingDate.isBetween(today, endOfToday, 'day', '[]')
        case 'week':
          return meetingDate.isBetween(today, endOfWeek, 'day', '[]')
        default:
          return true
      }
    })
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
    let comparison = 0
    switch (sortBy.value) {
      case 'date':
        comparison = new Date(a.start_time || '') - new Date(b.start_time || '')
        break
      case 'title':
        comparison = (a.title || '').localeCompare(b.title || '')
        break
    }
    return sortOrder.value === 'desc' ? -comparison : comparison
  })
  
  return filtered
})

const weekDays = computed(() => {
  const startOfWeek = currentWeek.value.clone().startOf('week')
  return Array.from({ length: 7 }, (_, i) => startOfWeek.clone().add(i, 'day'))
})

const getTimeSlotPosition = (hour, day) => {
  // Calculate accumulated height of previous slots
  let position = 0;
  for (let h = 0; h < hour; h++) {
    position += getTimeSlotHeight(h, day);
  }
  return position;
}

const getTimeSlotHeight = (hour, day) => {
  // Get meetings in this time slot
  const meetingsInSlot = getMeetingsInTimeSlot(day, hour);

  // Base height is 100/24 (normal hour height)
  const baseHeight = 100/24;
  
  // Increase height based on number of overlapping meetings
  return Math.max(baseHeight, baseHeight * Math.ceil(meetingsInSlot.length / 2));
}

const getTasksInSameSlot = (day, meeting) => {
  const meetingStartHour = moment(meeting.start_time).hour();
  return getMeetingsInTimeSlot(day, meetingStartHour);
}

const getTaskOffset = (index, totalMeetings) => {
  // Calculate left/right offsets for overlapping meetings
  const meetingWidth = 90; // percentage of slot width
  const overlap = 10; // percentage overlap between meetings
  
  if (totalMeetings <= 1) return '4px';
  
  const widthPerMeeting = meetingWidth / totalMeetings;
  const position = index * (widthPerMeeting - overlap);
  
  return position + '%';
}
</script>

<template>  <Layout>
    <div class="h-full space-y-6">      <!-- Header Section -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <!-- Left side -->
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Meetings</h1>
            <p class="mt-1 text-gray-600">Schedule and manage your meetings</p>
          </div>

          <!-- Right side -->
          <div class="flex items-center space-x-4">
            <!-- Search -->
            <div v-if="viewMode != 'calendar'" class="relative flex-1 lg:max-w-xs">              <input
                type="text"
                v-model="searchQuery"
                placeholder="Search meetings..."
                class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 pl-10 pr-4 py-2"
              />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>            
            <!-- View Options -->
            <div class="flex items-center space-x-2 border rounded-lg p-1">
              <button
                @click="viewMode = 'list'"
                :class="[
                  'p-2 rounded-md',
                  viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900'
                ]"
                title="List View (Ctrl + 1)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
              <button
                @click="viewMode = 'calendar'"
                :class="[
                  'p-2 rounded-md',
                  viewMode === 'calendar' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900'
                ]"
                title="Calendar View (Ctrl + 3)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
            </div>

            <!-- Sort Options -->
            <div v-if="viewMode != 'calendar'" class="flex items-center space-x-2">
              <select
                v-model="sortBy"
                class="rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="date">Sort by Date</option>
                <option value="title">Sort by Title</option>
              </select>
              <button
                @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
                class="p-2 rounded-md hover:bg-gray-100"
              >
                <!-- <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="{ 'rotate-180': sortOrder === 'desc' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                </svg> -->
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  :class="{ 'rotate-180': sortOrder === 'desc' }"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9M3 12h6" />
              </svg>
              </button>
            </div>

            <button
              @click="showNewMeetingModal = true"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Schedule Meeting
            </button>
          </div>
        </div>        <!-- Quick Filters -->
        <div class="mt-6 flex flex-wrap gap-4">
          <button 
            @click="selectedFilter = 'all'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2',
              selectedFilter === 'all' 
                ? 'bg-blue-50 text-blue-700 focus:ring-blue-500' 
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
            ]"
          >
            All Meetings
          </button>
          <button 
            @click="selectedFilter = 'today'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2',
              selectedFilter === 'today' 
                ? 'bg-blue-50 text-blue-700 focus:ring-blue-500' 
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
            ]"
          >
            Today
          </button>
          <button 
            @click="selectedFilter = 'week'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2',
              selectedFilter === 'week' 
                ? 'bg-blue-50 text-blue-700 focus:ring-blue-500' 
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
            ]"
          >
            This Week
          </button>
          <!-- <button 
            @click="selectedFilter = 'high-priority'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2',
              selectedFilter === 'high-priority' 
                ? 'bg-blue-50 text-blue-700 focus:ring-blue-500' 
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
            ]"
          >
            High Priority
          </button> -->
        </div>
      </div>      <!-- Meetings Content -->
      <div class="bg-white shadow rounded-lg overflow-hidden">
        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredMeetings.length === 0" class="flex flex-col items-center justify-center h-64">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 class="text-lg font-medium text-gray-900">No meetings found</h3>
          <p v-if="searchQuery" class="mt-1 text-gray-500">Try adjusting your search or filters</p>
          <p v-else class="mt-1 text-gray-500">Schedule your first meeting to get started!</p>
          <button
            @click="showNewMeetingModal = true"
            class="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Schedule Meeting
          </button>
        </div>

        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="overflow-x-auto">          <table class="min-w-full table-fixed divide-y divide-gray-300">
            <thead class="bg-gray-50">              <tr>
                <th scope="col" class="w-[35%] py-4 pl-6 pr-3 text-left text-sm font-semibold text-gray-900">Meeting Details</th>
                <th scope="col" class="w-[15%] py-4 pl-6 text-left text-sm font-semibold text-gray-900">Participants</th>
                <th scope="col" class="w-[25%] py-4 pl-6 text-left text-sm font-semibold text-gray-900">Time & Location</th>
                <!-- <th scope="col" class="w-[10%] py-4 pl-6 text-left text-sm font-semibold text-gray-900">Status</th> -->
                <th scope="col" class="w-[15%] py-4 pl-6 text-left text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="meeting in filteredMeetings" :key="meeting.id" class="hover:bg-gray-50 transition-colors duration-150">                <td class="py-4 pl-6 pr-3">
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <span class="text-blue-600 text-lg font-medium">
                          {{ meeting.title.charAt(0).toUpperCase() }}
                        </span>
                      </div>
                    </div>
                    <div class="min-w-0">
                      <div class="text-sm font-medium text-left text-gray-900 truncate">{{ meeting.title }}</div>
                      <div class="text-sm text-left text-gray-500 mt-1">{{ meeting.description || 'No description' }}</div>
                    </div>
                  </div>
                </td>
                <td class="py-4 pl-6">
                  <div class="flex items-center">
                    <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center border-2 border-white">
                      <span class="text-xs font-medium text-gray-600">You</span>
                    </div>
                  </div>
                </td>
                <td class="py-4 pl-6">
                  <div class="min-w-0">
                    <div class="text-sm text-left text-gray-900">
                      {{ formatDateTime(meeting.start_time) }}
                    </div>
                    <div class="text-sm text-left text-gray-500">
                      to {{ formatDateTime(meeting.end_time) }}
                    </div>
                    <div v-if="meeting.location" class="text-sm text-gray-500 mt-1 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span class="truncate">{{ meeting.location }}</span>
                    </div>
                  </div>
                </td>
                <!-- <td class="py-4 pl-6">
                  <div class="text-sm font-medium text-left bg-green-80 rounded-full text-green-800 truncate">Confirmed</div>
              
                </td>  -->
                         <!-- <span class="inline-flex px-2.5 py-0.5  rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Confirmed
                  </span> -->          
                <td class="py-4 pl-6">
                  <div class="flex items-center space-x-3">
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
                      @click="confirmDelete(meeting)"
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

        <!-- Calendar View -->
        <div v-else-if="viewMode === 'calendar'" class="p-6">
          <div class="flex flex-col h-[800px]">
            <!-- Calendar Header with Navigation -->
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium text-gray-900">
                {{ moment().format('MMMM YYYY') }}
              </h3>
              <div class="flex items-center space-x-4">
                <button
                  @click="currentWeek = currentWeek.clone().subtract(1, 'week')"
                  class="p-2 text-gray-400 hover:text-gray-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </button>
                <button
                  @click="currentWeek = moment()"
                  class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-md"
                >
                  Today
                </button>
                <button
                  @click="currentWeek = currentWeek.clone().add(1, 'week')"
                  class="p-2 text-gray-400 hover:text-gray-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>            <!-- Calendar Grid -->
            <div class="grid grid-cols-8 gap-px bg-gray-200 flex-1 rounded-lg overflow-y-auto max-h-[calc(100vh-16rem)]">
              <!-- Time Labels -->
              <div class="bg-white pt-3">
                <div class="sticky top-0 z-10 h-16 bg-white"></div>
                <div class="space-y-1">
                  <div v-for="hour in 24" :key="hour" class="relative h-16">
                    <span class="absolute -buttom-2 pt-1 right-2 text-xs text-gray-400">
                      {{ (hour - 1).toString().padStart(2, '0') }}:00
                    </span>
                  </div>
                </div>
              </div>

              <!-- Days -->
              <div v-for="day in weekDays" :key="day.format('YYYY-MM-DD')" class="bg-white relative">
                <!-- Day Header -->
                <div class="sticky top-0 z-10 bg-white border-b px-2 py-2 text-center h-13">
                  <span class="text-sm font-medium text-gray-900 block">{{ day.format('ddd') }}</span>
                  <span :class="[
                    'text-xs',
                    isToday(day) ? 'text-blue-600 font-medium' : 'text-gray-500'
                  ]">{{ day.format('D') }}</span>
                </div>                
                <!-- Time Slots -->
                <div class="relative h-[1152px]"> <!-- 24 hours * 48px = 1152px -->
                  <!-- todo -->
                  <div v-for="hour in 24" :key="hour" class="absolute w-full h-16 border-b border-gray-100" :style="{ top: `${(hour - 1) * 68}px` }">
                  </div>
                  <div v-for="meeting in filteredMeetings.filter(m => moment(m.start_time).isSame(day, 'day'))" 
                       :key="meeting.id"
                       class="absolute left-0 right-1 px-1 py-1 mx-1 rounded bg-blue-100 text-blue-800 text-xs hover:bg-blue-200 cursor-pointer "
                       :style="getMeetingPosition(meeting)"
                       @click="startEdit(meeting)"
                  >
                    <div class="font-medium truncate">{{ meeting.title }}</div>
                    <div class="text-xs opacity-75">
                      {{ formatTime(meeting.start_time) }} - {{ formatTime(meeting.end_time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
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

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg max-w-sm w-full p-6">
        <div class="flex items-center mb-4">
          <div class="flex-shrink-0 bg-red-100 rounded-full p-2 mr-3">
            <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900">Confirm Deletion</h3>
        </div>
        <!-- <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Deletion</h3> -->
        <p class="text-sm text-gray-500 mb-6">
          Are you sure you want to delete this meeting? This action cannot be undone.
        </p>        <div class="flex justify-end space-x-3">
          <button
            @click="deleteMeeting"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Delete Meeting
          </button>
          <button
            @click="showDeleteConfirm = false"
            class="mt-3 inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:mt-0 sm:text-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </Layout>
</template>
