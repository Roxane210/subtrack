document.addEventListener('alpine:init', () => {
  Alpine.data('subtrackApp', () => ({
    darkMode: localStorage.getItem('subtrack_theme') === 'dark' || (!('subtrack_theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches),
    
    // État principal
    dashboard: {
      total_monthly_cost: 0,
      total_yearly_cost: 0,
      active_count: 0,
      trial_count: 0,
      canceled_count: 0,
      upcoming_7_days_count: 0,
      category_distribution: {},
      upcoming_subscriptions: []
    },
    subscriptions: [],
    loading: true,
    
    // Filtres & Recherche
    filterCategory: 'all',
    filterStatus: 'all',
    searchQuery: '',
    
    // Modale Formulaire CRUD
    isModalOpen: false,
    modalMode: 'create', // 'create' ou 'edit'
    formData: {
      id: null,
      name: '',
      price: '',
      currency: '€',
      billing_cycle: 'monthly',
      next_billing_date: '',
      category: 'Streaming',
      payment_method: 'Carte Bancaire',
      status: 'active',
      cancellation_url: '',
      notes: ''
    },
    
    // Modale Import/Export
    isImportExportOpen: false,
    importType: 'json',
    notificationPerm: Notification.permission || 'default',

    // Menu contextuel (Clic Droit)
    contextMenu: {
      show: false,
      x: 0,
      y: 0,
      subscription: null
    },

    // Calendrier mensuel
    calendarYear: new Date().getFullYear(),
    calendarMonth: new Date().getMonth(), // 0 = Janvier, 11 = Décembre
    
    // Alert Toast
    toast: {
      show: false,
      message: '',
      type: 'success'
    },
    
    chartInstance: null,

    init() {
      this.applyTheme();
      this.fetchData();
      this.registerServiceWorker();

      // Fermer le menu contextuel lors d'un clic ailleurs ou d'un scroll
      window.addEventListener('click', () => {
        this.closeContextMenu();
      });
      window.addEventListener('scroll', () => {
        this.closeContextMenu();
      }, true);
    },

    toggleTheme() {
      this.darkMode = !this.darkMode;
      localStorage.setItem('subtrack_theme', this.darkMode ? 'dark' : 'light');
      this.applyTheme();
      if (this.chartInstance) {
        this.renderChart();
      }
    },

    applyTheme() {
      if (this.darkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },

    showToast(message, type = 'success') {
      this.toast.message = message;
      this.toast.type = type;
      this.toast.show = true;
      setTimeout(() => {
        this.toast.show = false;
      }, 4000);
    },

    async fetchData() {
      this.loading = true;
      try {
        const [dashRes, subsRes] = await Promise.all([
          fetch('/api/dashboard'),
          fetch(`/api/subscriptions?category=${this.filterCategory}&status=${this.filterStatus}&search=${encodeURIComponent(this.searchQuery)}`)
        ]);

        if (dashRes.ok && subsRes.ok) {
          this.dashboard = await dashRes.json();
          this.subscriptions = await subsRes.json();
          this.$nextTick(() => {
            this.renderChart();
          });
        }
      } catch (err) {
        console.error('Erreur de chargement des données:', err);
        this.showToast('Erreur lors du chargement des données', 'error');
      } finally {
        this.loading = false;
      }
    },

    applyFilters() {
      this.fetchData();
    },

    resetFilters() {
      this.filterCategory = 'all';
      this.filterStatus = 'all';
      this.searchQuery = '';
      this.fetchData();
    },

    openCreateModal() {
      this.modalMode = 'create';
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      this.formData = {
        id: null,
        name: '',
        price: '',
        currency: '€',
        billing_cycle: 'monthly',
        next_billing_date: tomorrow.toISOString().split('T')[0],
        category: 'Streaming',
        payment_method: 'Carte Bancaire',
        status: 'active',
        cancellation_url: '',
        notes: ''
      };
      this.isModalOpen = true;
    },

    openEditModal(sub) {
      this.modalMode = 'edit';
      this.formData = { ...sub };
      this.isModalOpen = true;
    },

    closeModal() {
      this.isModalOpen = false;
    },

    async saveSubscription() {
      if (!this.formData.name || !this.formData.price || !this.formData.next_billing_date) {
        this.showToast('Veuillez remplir les champs obligatoires.', 'error');
        return;
      }

      const payload = {
        name: this.formData.name,
        price: parseFloat(this.formData.price),
        currency: this.formData.currency,
        billing_cycle: this.formData.billing_cycle,
        next_billing_date: this.formData.next_billing_date,
        category: this.formData.category,
        payment_method: this.formData.payment_method,
        status: this.formData.status,
        cancellation_url: this.formData.cancellation_url || null,
        notes: this.formData.notes || null
      };

      try {
        let response;
        if (this.modalMode === 'create') {
          response = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } else {
          response = await fetch(`/api/subscriptions/${this.formData.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }

        if (response.ok) {
          this.showToast(this.modalMode === 'create' ? 'Abonnement créé avec succès !' : 'Abonnement mis à jour !', 'success');
          this.closeModal();
          this.fetchData();
        } else {
          const errData = await response.json();
          this.showToast(errData.detail || 'Une erreur est survenue', 'error');
        }
      } catch (err) {
        this.showToast('Erreur de connexion au serveur', 'error');
      }
    },

    // Gestion Menu Contextuel (Clic Droit)
    openContextMenu(event, sub) {
      event.preventDefault();
      event.stopPropagation();
      
      const menuWidth = 200;
      const menuHeight = 150;
      let posX = event.clientX;
      let posY = event.clientY;

      if (posX + menuWidth > window.innerWidth) {
        posX = window.innerWidth - menuWidth - 10;
      }
      if (posY + menuHeight > window.innerHeight) {
        posY = window.innerHeight - menuHeight - 10;
      }

      this.contextMenu = {
        show: true,
        x: posX,
        y: posY,
        subscription: sub
      };
    },

    closeContextMenu() {
      this.contextMenu.show = false;
      this.contextMenu.subscription = null;
    },

    async contextMenuRenew() {
      if (!this.contextMenu.subscription) return;
      const sub = this.contextMenu.subscription;
      this.closeContextMenu();
      await this.renewSubscription(sub);
    },

    contextMenuEdit() {
      if (!this.contextMenu.subscription) return;
      const sub = this.contextMenu.subscription;
      this.closeContextMenu();
      this.openEditModal(sub);
    },

    async contextMenuCancel() {
      if (!this.contextMenu.subscription) return;
      const sub = this.contextMenu.subscription;
      this.closeContextMenu();
      await this.cancelSubscription(sub);
    },

    async contextMenuDelete() {
      if (!this.contextMenu.subscription) return;
      const id = this.contextMenu.subscription.id;
      this.closeContextMenu();
      await this.deleteSubscription(id);
    },

    async renewSubscription(sub) {
      try {
        const response = await fetch(`/api/subscriptions/${sub.id}/renew`, {
          method: 'POST'
        });

        if (response.ok) {
          const updated = await response.json();
          this.showToast(`Abonnement "${sub.name}" renouvelé jusqu'au ${updated.next_billing_date} !`, 'success');
          this.fetchData();
        } else {
          const errData = await response.json();
          this.showToast(errData.detail || 'Erreur lors du renouvellement', 'error');
        }
      } catch (err) {
        this.showToast('Erreur de connexion au serveur', 'error');
      }
    },

    async cancelSubscription(sub) {
      if (!confirm(`Souhaitez-vous marquer l'abonnement "${sub.name}" comme résilié ? (Les données seront conservées dans l'historique sans futurs prélèvements)`)) {
        return;
      }

      try {
        const response = await fetch(`/api/subscriptions/${sub.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status: 'canceled'
          })
        });

        if (response.ok) {
          this.showToast(`"${sub.name}" a été marqué comme résilié.`, 'success');
          this.fetchData();
        } else {
          this.showToast('Erreur lors de la mise à jour du statut', 'error');
        }
      } catch (err) {
        this.showToast('Erreur de connexion au serveur', 'error');
      }
    },

    async deleteSubscription(id) {
      if (!confirm('Êtes-vous sûr de vouloir supprimer définitivement cet abonnement ?')) return;

      try {
        const response = await fetch(`/api/subscriptions/${id}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          this.showToast('Abonnement supprimé avec succès', 'success');
          this.fetchData();
        } else {
          this.showToast('Erreur lors de la suppression', 'error');
        }
      } catch (err) {
        this.showToast('Erreur de connexion au serveur', 'error');
      }
    },

    renderChart() {
      const ctx = document.getElementById('categoryChart');
      if (!ctx) return;

      const categories = Object.keys(this.dashboard.category_distribution || {});
      const values = Object.values(this.dashboard.category_distribution || {});

      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      if (categories.length === 0) {
        return;
      }

      const isDark = this.darkMode;
      const textColors = isDark ? '#94a3b8' : '#64748b';

      const palette = [
        '#6366f1', '#ec4899', '#3b82f6', '#10b981', '#f59e0b',
        '#8b5cf6', '#14b8a6', '#f43f5e', '#64748b'
      ];

      this.chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: categories,
          datasets: [{
            data: values,
            backgroundColor: palette.slice(0, categories.length),
            borderWidth: isDark ? 2 : 1,
            borderColor: isDark ? '#1e293b' : '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                color: textColors,
                boxWidth: 12,
                font: {
                  family: 'Inter',
                  size: 11
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  return ` ${context.label}: ${context.raw.toFixed(2)} €/mois`;
                }
              }
            }
          },
          cutout: '68%'
        }
      });
    },

    // ==========================================
    // LOGIQUE DU CALENDRIER MENSUEL
    // ==========================================
    get currentMonthName() {
      const date = new Date(this.calendarYear, this.calendarMonth, 1);
      const str = date.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
      return str.charAt(0).toUpperCase() + str.slice(1);
    },

    prevCalendarMonth() {
      if (this.calendarMonth === 0) {
        this.calendarMonth = 11;
        this.calendarYear -= 1;
      } else {
        this.calendarMonth -= 1;
      }
      this.$nextTick(() => {
        if (window.lucide) window.lucide.createIcons();
      });
    },

    nextCalendarMonth() {
      if (this.calendarMonth === 11) {
        this.calendarMonth = 0;
        this.calendarYear += 1;
      } else {
        this.calendarMonth += 1;
      }
      this.$nextTick(() => {
        if (window.lucide) window.lucide.createIcons();
      });
    },

    goToCurrentMonth() {
      const now = new Date();
      this.calendarYear = now.getFullYear();
      this.calendarMonth = now.getMonth();
      this.$nextTick(() => {
        if (window.lucide) window.lucide.createIcons();
      });
    },

    // Calcule les occurrences effectives d'un abonnement pour le mois affiché
    getSubOccurrencesInMonth(sub, year, month) {
      if (sub.status === 'canceled') return [];

      const parts = sub.next_billing_date.split('-');
      if (parts.length !== 3) return [];
      const baseYear = parseInt(parts[0], 10);
      const baseMonth = parseInt(parts[1], 10) - 1; // 0-indexed
      const baseDay = parseInt(parts[2], 10);

      const startDate = new Date(baseYear, baseMonth, baseDay);
      const cycle = (sub.billing_cycle || 'monthly').toLowerCase();
      const occurrences = [];

      const targetMonthStart = new Date(year, month, 1);
      const targetMonthEnd = new Date(year, month + 1, 0); // Dernier jour du mois

      // Si l'abonnement commence après la fin du mois ciblé, pas d'occurrence
      if (startDate > targetMonthEnd) return [];

      if (cycle === 'monthly') {
        const maxDay = targetMonthEnd.getDate();
        const actualDay = Math.min(baseDay, maxDay);
        const occurrenceDate = new Date(year, month, actualDay);
        if (occurrenceDate >= startDate) {
          occurrences.push(occurrenceDate);
        }
      } else if (cycle === 'yearly') {
        if (baseMonth === month) {
          const maxDay = targetMonthEnd.getDate();
          const actualDay = Math.min(baseDay, maxDay);
          const occurrenceDate = new Date(year, month, actualDay);
          if (occurrenceDate >= startDate) {
            occurrences.push(occurrenceDate);
          }
        }
      } else if (cycle === 'quarterly') {
        let diffMonths = (year - baseYear) * 12 + (month - baseMonth);
        if (diffMonths >= 0 && diffMonths % 3 === 0) {
          const maxDay = targetMonthEnd.getDate();
          const actualDay = Math.min(baseDay, maxDay);
          const occurrenceDate = new Date(year, month, actualDay);
          if (occurrenceDate >= startDate) {
            occurrences.push(occurrenceDate);
          }
        }
      } else if (cycle === 'semiannual') {
        let diffMonths = (year - baseYear) * 12 + (month - baseMonth);
        if (diffMonths >= 0 && diffMonths % 6 === 0) {
          const maxDay = targetMonthEnd.getDate();
          const actualDay = Math.min(baseDay, maxDay);
          const occurrenceDate = new Date(year, month, actualDay);
          if (occurrenceDate >= startDate) {
            occurrences.push(occurrenceDate);
          }
        }
      } else if (cycle === 'weekly') {
        let cur = new Date(startDate.getTime());
        // Avancer rapidement si loin dans le passé
        if (cur < targetMonthStart) {
          const diffDays = Math.floor((targetMonthStart.getTime() - cur.getTime()) / (1000 * 60 * 60 * 24));
          const weeksToAdvance = Math.floor(diffDays / 7);
          cur.setDate(cur.getDate() + weeksToAdvance * 7);
        }
        while (cur <= targetMonthEnd) {
          if (cur >= targetMonthStart && cur >= startDate) {
            occurrences.push(new Date(cur.getTime()));
          }
          cur.setDate(cur.getDate() + 7);
        }
      }

      return occurrences;
    },

    // Génère le tableau des jours du mois avec leurs abonnements associés
    get calendarDays() {
      const year = this.calendarYear;
      const month = this.calendarMonth;

      const firstDayOfMonth = new Date(year, month, 1);
      const lastDayOfMonth = new Date(year, month + 1, 0);
      const numDays = lastDayOfMonth.getDate();

      // Jour de la semaine (0 = Dimanche, 1 = Lundi, ..., 6 = Samedi)
      // Ajustement pour faire commencer la semaine le Lundi (0 = Lundi, 6 = Dimanche)
      let firstDayWeekday = firstDayOfMonth.getDay() - 1;
      if (firstDayWeekday < 0) firstDayWeekday = 6;

      const today = new Date();
      const isCurrentRealMonth = today.getFullYear() === year && today.getMonth() === month;
      const todayDate = today.getDate();

      // Pré-calculer les abonnements par jour du mois (1 à numDays)
      const subsByDay = {};
      for (let d = 1; d <= numDays; d++) {
        subsByDay[d] = [];
      }

      const activeSubs = (this.subscriptions || []).filter(s => s.status !== 'canceled');
      for (const sub of activeSubs) {
        const occs = this.getSubOccurrencesInMonth(sub, year, month);
        for (const occ of occs) {
          const d = occ.getDate();
          if (subsByDay[d]) {
            subsByDay[d].push({
              ...sub,
              occurrenceDateStr: `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
            });
          }
        }
      }

      const daysArray = [];

      // Cases vides avant le 1er du mois
      for (let i = 0; i < firstDayWeekday; i++) {
        daysArray.push({
          dayNumber: '',
          isCurrentMonth: false,
          isToday: false,
          subscriptions: []
        });
      }

      // Jours du mois
      for (let day = 1; day <= numDays; day++) {
        daysArray.push({
          dayNumber: day,
          isCurrentMonth: true,
          isToday: isCurrentRealMonth && day === todayDate,
          subscriptions: subsByDay[day] || []
        });
      }

      // Compléter pour avoir une grille propre (multiple de 7)
      while (daysArray.length % 7 !== 0) {
        daysArray.push({
          dayNumber: '',
          isCurrentMonth: false,
          isToday: false,
          subscriptions: []
        });
      }

      return daysArray;
    },

    // Total des dépenses prévues pour le mois affiché
    get calendarMonthTotal() {
      let total = 0;
      const days = this.calendarDays;
      for (const day of days) {
        if (day.isCurrentMonth && day.subscriptions) {
          for (const s of day.subscriptions) {
            total += s.price;
          }
        }
      }
      return total.toFixed(2);
    },

    // Total des opérations du mois affiché
    get calendarMonthOperationsCount() {
      let count = 0;
      const days = this.calendarDays;
      for (const day of days) {
        if (day.isCurrentMonth && day.subscriptions) {
          count += day.subscriptions.length;
        }
      }
      return count;
    },

    // Gestion des notifications PWA
    async requestNotificationPermission() {
      if (!('Notification' in window)) {
        this.showToast("Ce navigateur ne prend pas en charge les notifications.", "error");
        return;
      }

      const permission = await Notification.requestPermission();
      this.notificationPerm = permission;
      if (permission === 'granted') {
        this.showToast('Notifications activées !', 'success');
        if (this.dashboard.upcoming_7_days_count > 0) {
          new Notification('SubTrack Alert', {
            body: `Vous avez ${this.dashboard.upcoming_7_days_count} abonnement(s) renouvelé(s) dans les 7 prochains jours !`,
            icon: '/static/icons/icon-192.png'
          });
        }
      } else {
        this.showToast('Permission de notification refusée.', 'warning');
      }
    },

    // Import / Export
    async uploadImportFile(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      const endpoint = this.importType === 'json' ? '/api/import/json' : '/api/import/csv';
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData
        });
        const result = await response.json();
        if (response.ok) {
          this.showToast(result.message || 'Importation réussie !', 'success');
          this.isImportExportOpen = false;
          this.fetchData();
        } else {
          this.showToast(result.detail || 'Erreur lors de l’importation', 'error');
        }
      } catch (err) {
        this.showToast('Erreur lors de l’envoi du fichier', 'error');
      } finally {
        event.target.value = '';
      }
    },

    registerServiceWorker() {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
          .then((reg) => {
            console.log('Service Worker enregistré avec succès:', reg.scope);
          })
          .catch((err) => {
            console.warn('Échec d’enregistrement du Service Worker:', err);
          });
      }
    }
  }));
});
