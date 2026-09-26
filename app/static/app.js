// ============================================================
// Travel Booking System — Frontend Logic (JavaScript)
// ============================================================
// Kết nối trực tiếp Backend REST APIs: Auth, Tours, Bookings.
// Hỗ trợ tự động tính tiền, quản lý JWT token, lưu trữ cục bộ.
// ============================================================

const API_BASE = '/api/v1';

// State toàn cục
let state = {
  token: localStorage.getItem('access_token') || '',
  user: JSON.parse(localStorage.getItem('user_info') || 'null'),
  tours: [],
  selectedTour: null,
  bookAdults: 1,
  bookChildren: 0,
};

// Fallback tours nếu DB chưa có dữ liệu để giao diện luôn lung linh
const DEMO_TOURS = [
  {
    id: "f1a2b3c4-0001-4000-8000-000000000001",
    title: "Vịnh Hạ Long 3 Ngày 2 Đêm — Du Thuyền 5 Sao",
    description: "Khám phá di sản thiên nhiên thế giới UNESCO, chèo kayak qua hang Luồn, tắm biển đảo Ti Tốp và thưởng thức tiệc nướng hoàng hôn trên vịnh.",
    category: "Adventure",
    destination: "Vịnh Hạ Long, Quảng Ninh",
    base_price_adult: 250.00,
    base_price_child: 125.00,
    max_participants: 30,
    start_date: "2027-04-15",
    end_date: "2027-04-18",
    image: "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=800&q=80",
    itineraries: [
      {
        day_number: 1,
        title: "Ngày 1: Hà Nội - Vịnh Hạ Long & Ngắm Hoàng Hôn",
        activities: [
          { time: "08:00", place_name: "Phố Cổ Hà Nội", description: "Xe limousine đón quý khách khởi hành đi Hạ Long." },
          { time: "12:00", place_name: "Cảng Tuần Châu", description: "Lên du thuyền thưởng thức đồ uống chào mừng và nhận phòng nghỉ." },
          { time: "15:00", place_name: "Hang Sửng Sốt", description: "Khám phá hang động thạch nhũ kỳ vĩ nhất vịnh." }
        ]
      },
      {
        day_number: 2,
        title: "Ngày 2: Chèo Kayak Hang Luồn & Đảo Ti Tốp",
        activities: [
          { time: "07:00", place_name: "Sundeck Du Thuyền", description: "Tập thái cực quyền đón bình minh trên vịnh." },
          { time: "09:30", place_name: "Hang Luồn", description: "Trải nghiệm chèo thuyền kayak ngắm khỉ hoang dã." },
          { time: "14:00", place_name: "Đảo Ti Tốp", description: "Tắm biển và chinh phục đỉnh Ti Tốp ngắm toàn cảnh 360 độ." }
        ]
      },
      {
        day_number: 3,
        title: "Ngày 3: Làng Chài Cửa Vạn - Trở Về Hà Nội",
        activities: [
          { time: "08:30", place_name: "Làng Chài Cửa Vạn", description: "Tìm hiểu cuộc sống văn hóa của cư dân vạn chài." },
          { time: "11:30", place_name: "Cảng Tuần Châu", description: "Cập bến, xe đưa quý khách trở về trung tâm Hà Nội." }
        ]
      }
    ]
  },
  {
    id: "f1a2b3c4-0002-4000-8000-000000000002",
    title: "Đà Nẵng - Hội An - Bà Nà Hills 4 Ngày 3 Đêm",
    description: "Khám phá Cầu Vàng lơ lửng giữa mây ngàn, phố cổ đèn lồng Hội An lung linh về đêm và bãi biển Mỹ Khê tuyệt đẹp.",
    category: "Beach & Resort",
    destination: "Đà Nẵng & Hội An",
    base_price_adult: 180.00,
    base_price_child: 90.00,
    max_participants: 25,
    start_date: "2027-05-10",
    end_date: "2027-05-14",
    image: "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=800&q=80",
    itineraries: [
      {
        day_number: 1,
        title: "Ngày 1: Đón Sân Bay - Biển Mỹ Khê - Cầu Rồng",
        activities: [
          { time: "10:00", place_name: "Sân bay Đà Nẵng", description: "Đón đoàn về khách sạn nhận phòng nghỉ ngơi." },
          { time: "16:00", place_name: "Bãi biển Mỹ Khê", description: "Tự do tắm biển và thưởng thức hải sản tươi sống." }
        ]
      },
      {
        day_number: 2,
        title: "Ngày 2: Bà Nà Hills & Check-in Cầu Vàng",
        activities: [
          { time: "08:00", place_name: "Bà Nà Hills", description: "Đi cáp treo đạt kỷ lục thế giới, check-in Cầu Vàng bàn tay khổng lồ." }
        ]
      }
    ]
  },
  {
    id: "f1a2b3c4-0003-4000-8000-000000000003",
    title: "Phú Quốc Thiên Đường Đảo Ngọc 3 Ngày 2 Đêm",
    description: "Trải nghiệm cáp treo Hòn Thơm vượt biển dài nhất thế giới, lặn ngắm san hô rực rỡ và ngắm hoàng hôn Grand World.",
    category: "Beach & Resort",
    destination: "Phú Quốc, Kiên Giang",
    base_price_adult: 220.00,
    base_price_child: 110.00,
    max_participants: 20,
    start_date: "2027-06-01",
    end_date: "2027-06-04",
    image: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=800&q=80",
    itineraries: [
      {
        day_number: 1,
        title: "Ngày 1: Check-in Sunset Sanato - Grand World",
        activities: [
          { time: "14:00", place_name: "Grand World Phú Quốc", description: "Thành phố không ngủ, ngắm show diễn nhạc nước tinh hoa Việt Nam." }
        ]
      }
    ]
  }
];

// ================= KHỞI TẠO KHI TẢI TRANG =================
document.addEventListener('DOMContentLoaded', () => {
  renderNavActions();
  fetchTours();
  setupEventListeners();
});

// ================= GIAO TIẾP VỚI API TOURS =================
async function fetchTours(filters = {}) {
  const grid = document.getElementById('toursGrid');
  grid.innerHTML = `
    <div class="loading-state">
      <i class="fa-solid fa-circle-notch fa-spin"></i>
      <p>Đang tìm kiếm hành trình phù hợp...</p>
    </div>
  `;

  try {
    let url = `${API_BASE}/tours?page=1&page_size=20`;
    if (filters.destination) url += `&destination=${encodeURIComponent(filters.destination)}`;
    if (filters.category) url += `&category=${encodeURIComponent(filters.category)}`;
    if (filters.max_price) url += `&max_price=${filters.max_price}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('API fetch failed');
    const data = await res.json();

    if (data.items && data.items.length > 0) {
      state.tours = data.items;
    } else {
      // Dùng dữ liệu demo nếu DB chưa có tour
      state.tours = filterLocalDemos(filters);
    }
  } catch (err) {
    console.warn('API tour offline, dùng demo data:', err);
    state.tours = filterLocalDemos(filters);
  }

  renderToursGrid(state.tours);
}

function filterLocalDemos(filters) {
  return DEMO_TOURS.filter(t => {
    if (filters.destination && !t.destination.toLowerCase().includes(filters.destination.toLowerCase())) return false;
    if (filters.category && t.category !== filters.category) return false;
    if (filters.max_price && t.base_price_adult > Number(filters.max_price)) return false;
    return true;
  });
}

function renderToursGrid(tours) {
  const grid = document.getElementById('toursGrid');
  if (!tours || tours.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-map-location"></i>
        <h3>Không tìm thấy chuyến đi phù hợp</h3>
        <p>Thử tìm kiếm với từ khóa khác hoặc bỏ bớt bộ lọc bạn nhé!</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = tours.map((tour, idx) => {
    const imgUrl = tour.image || DEMO_TOURS[idx % DEMO_TOURS.length].image;
    return `
      <div class="tour-card">
        <div class="tour-img-wrap">
          <img src="${imgUrl}" alt="${tour.title}" class="tour-img" loading="lazy">
          <span class="tour-category-tag">${tour.category || 'Tour Khám Phá'}</span>
          <span class="tour-duration-tag"><i class="fa-regular fa-clock"></i> 3N2Đ</span>
        </div>
        <div class="tour-info">
          <div class="tour-destination">
            <i class="fa-solid fa-location-dot"></i> ${tour.destination}
          </div>
          <h3 class="tour-title">${tour.title}</h3>
          <p class="tour-description">${tour.description}</p>
          
          <div class="tour-footer">
            <div class="tour-price-box">
              <span class="price-sub">Giá từ</span>
              <span class="price-amount">$${Number(tour.base_price_adult).toFixed(0)}</span>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline" onclick="openTourDetail('${tour.id}')">
                <i class="fa-solid fa-circle-info"></i> Lịch Trình
              </button>
              <button class="btn btn-primary" onclick="openBookingModal('${tour.id}')">
                <i class="fa-solid fa-ticket"></i> Đặt Vé
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ================= CHI TIẾT TOUR MODAL =================
async function openTourDetail(tourId) {
  let tour = state.tours.find(t => t.id === tourId);
  if (!tour) tour = DEMO_TOURS.find(t => t.id === tourId) || DEMO_TOURS[0];

  try {
    const res = await fetch(`${API_BASE}/tours/${tourId}`);
    if (res.ok) {
      tour = await res.json();
    }
  } catch (e) {
    // fallback
  }

  state.selectedTour = tour;

  document.getElementById('modalTourCategory').textContent = tour.category || 'Adventure';
  document.getElementById('modalTourTitle').textContent = tour.title;
  document.getElementById('modalTourDestination').textContent = tour.destination;
  document.getElementById('modalTourMaxPax').textContent = `${tour.max_participants || 30} khách tối đa`;
  document.getElementById('modalTourDates').textContent = `${tour.start_date} → ${tour.end_date}`;
  document.getElementById('modalTourDesc').textContent = tour.description;
  document.getElementById('modalTourPrice').textContent = `$${Number(tour.base_price_adult).toFixed(2)}`;

  // Render Itinerary Timeline
  const itineraryBox = document.getElementById('modalTourItinerary');
  const itineraries = tour.itineraries || DEMO_TOURS[0].itineraries;

  if (itineraries && itineraries.length > 0) {
    itineraryBox.innerHTML = itineraries.map(day => `
      <div class="timeline-day">
        <h4 class="timeline-day-title">${day.title || `Ngày ${day.day_number}`}</h4>
        ${(day.activities || []).map(act => `
          <div class="timeline-activity">
            <span class="activity-time"><i class="fa-regular fa-clock"></i> ${act.time || '08:00'}</span>
            <strong>${act.place_name}</strong>: ${act.description}
          </div>
        `).join('')}
      </div>
    `).join('');
  } else {
    itineraryBox.innerHTML = `<p class="text-muted">Lịch trình chi tiết đang được cập nhật thêm.</p>`;
  }

  document.getElementById('modalBookNowBtn').onclick = () => {
    closeModal('tourDetailModal');
    openBookingModal(tour.id);
  };

  openModal('tourDetailModal');
}

// ================= MODAL ĐẶT TOUR & TÍNH TIỀN =================
function openBookingModal(tourId) {
  let tour = state.tours.find(t => t.id === tourId);
  if (!tour) tour = DEMO_TOURS.find(t => t.id === tourId) || DEMO_TOURS[0];
  state.selectedTour = tour;

  // Điền thông tin tour vào form
  document.getElementById('bookModalTourTitle').textContent = tour.title;
  document.getElementById('bookModalTourDest').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${tour.destination}`;
  document.getElementById('labelAdultPrice').textContent = `$${Number(tour.base_price_adult).toFixed(2)} / vé`;
  document.getElementById('labelChildPrice').textContent = `$${Number(tour.base_price_child).toFixed(2)} / vé`;

  // Reset counters
  state.bookAdults = 1;
  state.bookChildren = 0;
  document.getElementById('bookNumAdults').value = 1;
  document.getElementById('bookNumChildren').value = 0;

  // Tự điền thông tin nếu đã đăng nhập
  if (state.user) {
    document.getElementById('bookContactName').value = state.user.full_name || '';
    document.getElementById('bookContactEmail').value = state.user.email || '';
  }

  updateLiveTotal();
  openModal('bookingModal');
}

function changePax(type, delta) {
  if (type === 'adult') {
    state.bookAdults = Math.max(1, Math.min(30, state.bookAdults + delta));
    document.getElementById('bookNumAdults').value = state.bookAdults;
  } else {
    state.bookChildren = Math.max(0, Math.min(30, state.bookChildren + delta));
    document.getElementById('bookNumChildren').value = state.bookChildren;
  }
  updateLiveTotal();
}

function updateLiveTotal() {
  if (!state.selectedTour) return;
  const adultPrice = Number(state.selectedTour.base_price_adult) || 250;
  const childPrice = Number(state.selectedTour.base_price_child) || 125;
  const total = (state.bookAdults * adultPrice) + (state.bookChildren * childPrice);
  document.getElementById('bookTotalDisplay').textContent = `$${total.toFixed(2)}`;
}

// Xử lý gửi đặt tour (POST /api/v1/bookings)
document.getElementById('bookingForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  if (!state.token) {
    showToast('Vui lòng đăng nhập trước khi đặt tour nhé!', 'error');
    openModal('authModal');
    return;
  }

  const payload = {
    tour_id: state.selectedTour.id,
    num_adults: state.bookAdults,
    num_children: state.bookChildren,
    contact_name: document.getElementById('bookContactName').value.trim(),
    contact_email: document.getElementById('bookContactEmail').value.trim(),
    contact_phone: document.getElementById('bookContactPhone').value.trim(),
    special_requests: document.getElementById('bookSpecialRequests').value.trim() || null,
    passengers: []
  };

  const btnSubmit = document.getElementById('btnSubmitBooking');
  btnSubmit.disabled = true;
  btnSubmit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý...`;

  try {
    const res = await fetch(`${API_BASE}/bookings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error?.message || 'Không thể tạo đơn đặt tour');
    }

    closeModal('bookingModal');
    showToast(`🎉 Đặt tour thành công! Mã đơn: ${data.booking_code}`);
    openMyBookings();
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, 'error');
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `<i class="fa-solid fa-check"></i> Xác Nhận Đặt Tour`;
  }
});

// ================= MY BOOKINGS (LỊCH SỬ ĐẶT TOUR) =================
async function openMyBookings() {
  if (!state.token) {
    showToast('Vui lòng đăng nhập để xem đơn của bạn!', 'error');
    openModal('authModal');
    return;
  }

  openModal('myBookingsModal');
  const container = document.getElementById('myBookingsContainer');
  container.innerHTML = `
    <div class="loading-state">
      <i class="fa-solid fa-spinner fa-spin"></i>
      <p>Đang tải đơn đặt tour của bạn...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/bookings/my?page=1&page_size=20`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const data = await res.json();

    if (!res.ok || !data.items || data.items.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-ticket-simple"></i>
          <p>Bạn chưa có đơn đặt tour nào. Hãy đặt chuyến đi đầu tiên ngay!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = data.items.map(b => {
      let statusClass = 'status-pending';
      let statusText = 'Chờ Thanh Toán';
      if (b.status === 'CONFIRMED') {
        statusClass = 'status-confirmed';
        statusText = 'Đã Xác Nhận';
      } else if (b.status === 'CANCELLED') {
        statusClass = 'status-cancelled';
        statusText = 'Đã Hủy';
      }

      return `
        <div class="booking-card-item">
          <div class="booking-item-info">
            <span class="booking-item-code">MÃ ĐƠN: ${b.booking_code}</span>
            <h4>${b.tour_title || 'Tour Du Lịch'}</h4>
            <span class="text-dim"><i class="fa-solid fa-user-group"></i> ${b.num_adults} người lớn, ${b.num_children} trẻ em</span>
          </div>
          <div>
            <span class="status-badge ${statusClass}">${statusText}</span>
          </div>
          <div>
            <div class="booking-item-price">$${Number(b.total_price).toFixed(2)}</div>
          </div>
          <div>
            ${b.status !== 'CANCELLED' ? `
              <button class="btn btn-outline btn-danger btn-sm" onclick="cancelBooking('${b.id}')">
                Hủy Đơn
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Lỗi khi tải danh sách đơn: ${err.message}</p>`;
  }
}

async function cancelBooking(bookingId) {
  if (!confirm('Bạn có chắc chắn muốn hủy đơn đặt tour này không? Chỗ trống sẽ được giải phóng cho khách khác.')) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/bookings/${bookingId}/cancel`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error('Không thể hủy đơn');
    showToast('Đã hủy đơn đặt tour thành công!');
    openMyBookings();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ================= AUTHENTICATION (LOGIN / REGISTER) =================
function renderNavActions() {
  const container = document.getElementById('navActions');
  if (state.token && state.user) {
    const initial = (state.user.full_name || 'U').charAt(0).toUpperCase();
    container.innerHTML = `
      <div class="user-badge">
        <div class="user-avatar">${initial}</div>
        <span class="user-name-text">${state.user.full_name}</span>
      </div>
      <button class="btn btn-outline" onclick="logout()"><i class="fa-solid fa-arrow-right-from-bracket"></i> Đăng Xuất</button>
    `;
  } else {
    container.innerHTML = `
      <button class="btn btn-outline" id="loginBtn" onclick="openModal('authModal'); switchAuthTab('login')">
        <i class="fa-solid fa-right-to-bracket"></i> Đăng Nhập
      </button>
      <button class="btn btn-primary" id="registerBtn" onclick="openModal('authModal'); switchAuthTab('register')">
        <i class="fa-solid fa-user-plus"></i> Đăng Ký
      </button>
    `;
  }
}

function switchAuthTab(tab) {
  if (tab === 'login') {
    document.getElementById('tabLogin').classList.add('active');
    document.getElementById('tabRegister').classList.remove('active');
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('registerForm').classList.add('hidden');
  } else {
    document.getElementById('tabRegister').classList.add('active');
    document.getElementById('tabLogin').classList.remove('active');
    document.getElementById('registerForm').classList.remove('hidden');
    document.getElementById('loginForm').classList.add('hidden');
  }
}

function fillDemoAdmin() {
  document.getElementById('loginEmail').value = 'admin@travelbooking.com';
  document.getElementById('loginPassword').value = 'Admin@123456';
  showToast('Đã điền thông tin tài khoản Admin mẫu!');
}

// Submit Login
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value.trim();

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Đăng nhập thất bại');

    state.token = data.access_token;
    localStorage.setItem('access_token', data.access_token);

    // Lấy profile user
    const profileRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${data.access_token}` }
    });
    if (profileRes.ok) {
      state.user = await profileRes.json();
      localStorage.setItem('user_info', JSON.stringify(state.user));
    }

    closeModal('authModal');
    renderNavActions();
    showToast(`Chào mừng ${state.user?.full_name || 'bạn'} đã đăng nhập!`);
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Submit Register
document.getElementById('registerForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const full_name = document.getElementById('regFullName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value.trim();

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Đăng ký thất bại');

    showToast('Tài khoản đã tạo thành công! Hãy đăng nhập ngay.');
    switchAuthTab('login');
    document.getElementById('loginEmail').value = email;
    document.getElementById('loginPassword').value = password;
  } catch (err) {
    showToast(err.message, 'error');
  }
});

function logout() {
  state.token = '';
  state.user = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
  renderNavActions();
  showToast('Đã đăng xuất tài khoản thành công!');
}

// ================= MODAL & EVENT HELPERS =================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('show');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('show');
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'}"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function setupEventListeners() {
  // Tìm kiếm tour
  document.getElementById('btnSearchTours').addEventListener('click', () => {
    const destination = document.getElementById('filterDestination').value.trim();
    const category = document.getElementById('filterCategory').value;
    const max_price = document.getElementById('filterMaxPrice').value;
    fetchTours({ destination, category, max_price });
  });

  // Category pills filter
  document.getElementById('categoryPills').addEventListener('click', (e) => {
    if (e.target.classList.contains('pill')) {
      document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      const category = e.target.dataset.category;
      fetchTours({ category });
    }
  });

  // My bookings button in nav
  document.getElementById('myBookingsNavBtn').addEventListener('click', openMyBookings);

  // Close modals on clicking outside
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('show');
    });
  });
}
