/* Hijri / Gregorian conversion (Kuwaiti tabular algorithm).
   Mirrors app/utils/hijri.py so server and client agree to ±1 day. */
(function (root) {
    'use strict';

    var HIJRI_MONTHS_AR = [
        'محرم','صفر','ربيع الأول','ربيع الآخر','جمادى الأولى','جمادى الآخرة',
        'رجب','شعبان','رمضان','شوال','ذو القعدة','ذو الحجة'
    ];

    function gregorianToHijri(gy, gm, gd) {
        var y = gy, m = gm;
        if (gm < 3) { y = gy - 1; m = gm + 12; }
        var a = Math.floor(y / 100);
        var b = 2 - a + Math.floor(a / 4);
        var jd = Math.floor(365.25 * (y + 4716))
               + Math.floor(30.6001 * (m + 1))
               + gd + b - 1524;
        var l = jd - 1948440 + 10632;
        var n = Math.floor((l - 1) / 10631);
        l = l - 10631 * n + 354;
        var j = (Math.floor((10985 - l) / 5316))
              * (Math.floor((50 * l) / 17719))
              + (Math.floor(l / 5670))
              * (Math.floor((43 * l) / 15238));
        l = l - (Math.floor((30 - j) / 15)) * (Math.floor((17719 * j) / 50))
              - (Math.floor(j / 16)) * (Math.floor((15238 * j) / 43)) + 29;
        var hm = Math.floor((24 * l) / 709);
        var hd = l - Math.floor((709 * hm) / 24);
        var hy = 30 * n + j - 30;
        return { year: hy, month: hm, day: hd };
    }

    function hijriToGregorian(hy, hm, hd) {
        // Inverse via JD: build JD from Hijri, then JD → Gregorian.
        var jd = Math.floor((11 * hy + 3) / 30)
               + 354 * hy
               + 30 * hm
               - Math.floor((hm - 1) / 2)
               + hd + 1948440 - 385;
        // JD → Gregorian (Meeus)
        var z = jd + 0.5;
        var Z = Math.floor(z);
        var A;
        if (Z < 2299161) { A = Z; }
        else {
            var alpha = Math.floor((Z - 1867216.25) / 36524.25);
            A = Z + 1 + alpha - Math.floor(alpha / 4);
        }
        var B = A + 1524;
        var C = Math.floor((B - 122.1) / 365.25);
        var D = Math.floor(365.25 * C);
        var E = Math.floor((B - D) / 30.6001);
        var day = B - D - Math.floor(30.6001 * E);
        var month = E < 14 ? E - 1 : E - 13;
        var year = month > 2 ? C - 4716 : C - 4715;
        return { year: year, month: month, day: day };
    }

    function formatHijri(gy, gm, gd) {
        var h = gregorianToHijri(gy, gm, gd);
        var dd = String(h.day).padStart(2, '0');
        var mm = String(h.month).padStart(2, '0');
        return dd + '/' + mm + '/' + h.year + ' هـ';
    }

    function formatGregorian(g) {
        var dd = String(g.day).padStart(2, '0');
        var mm = String(g.month).padStart(2, '0');
        return g.year + '-' + mm + '-' + dd;
    }

    function isValidHijri(y, m, d) {
        if (!Number.isInteger(y) || !Number.isInteger(m) || !Number.isInteger(d)) return false;
        if (y < 1300 || y > 1500) return false;
        if (m < 1 || m > 12) return false;
        if (d < 1 || d > 30) return false;
        return true;
    }

    /**
     * Wire a Hijri / Gregorian toggle on a form field.
     *
     * Inputs (DOM ids, all required):
     *   gregInputId   — <input type="date"> that holds the canonical Gregorian
     *                   value and is what the form actually submits.
     *   hijriBoxId    — wrapper element that contains day/month/year inputs.
     *   hDayId, hMonthId, hYearId — Hijri inputs (number, select, number).
     *   convLabelId   — <small>/<div> for the live conversion / error feedback.
     *   radioName     — name of the two-button radio group ('h' | 'g').
     *
     * Options:
     *   defaultMode   — 'h' or 'g'  (default: 'h')
     *   prefillToday  — fill Hijri inputs with today's date if nothing set
     *                   (default: false)
     *   onChange(g)   — optional callback fired whenever the Gregorian value
     *                   changes (receives 'YYYY-MM-DD' or '').
     */
    function bindHijriToggle(opts) {
        var g = document.getElementById(opts.gregInputId);
        var box = document.getElementById(opts.hijriBoxId);
        var hY = document.getElementById(opts.hYearId);
        var hM = document.getElementById(opts.hMonthId);
        var hD = document.getElementById(opts.hDayId);
        var conv = document.getElementById(opts.convLabelId);
        var radios = document.querySelectorAll('input[name="' + opts.radioName + '"]');
        if (!g || !box || !hY || !hM || !hD || !conv) return;

        // Populate month dropdown once.
        if (!hM.options.length) {
            HIJRI_MONTHS_AR.forEach(function (name, i) {
                var o = document.createElement('option');
                o.value = i + 1;
                o.textContent = (i + 1) + ' - ' + name;
                hM.appendChild(o);
            });
        }

        function setConv(text, cls) {
            conv.textContent = text;
            conv.className = 'form-text ' + (cls || '');
        }

        function prefillHijriFromGreg(val) {
            var parts = (val || '').split('-');
            if (parts.length !== 3) return false;
            var h = gregorianToHijri(+parts[0], +parts[1], +parts[2]);
            hY.value = h.year; hM.value = h.month; hD.value = h.day;
            setConv('الميلادي: ' + val, 'text-success');
            return true;
        }

        function syncFromHijri() {
            var y = parseInt(hY.value, 10);
            var m = parseInt(hM.value, 10);
            var d = parseInt(hD.value, 10);
            if (!y && !m && !d) {
                setConv('', '');
                g.value = '';
                if (opts.onChange) opts.onChange('');
                return;
            }
            if (!isValidHijri(y, m, d)) {
                setConv('تاريخ هجري غير صحيح', 'text-danger');
                g.value = '';
                if (opts.onChange) opts.onChange('');
                return;
            }
            var gd = hijriToGregorian(y, m, d);
            var gStr = formatGregorian(gd);
            g.value = gStr;
            setConv('الميلادي: ' + gStr, 'text-success');
            if (opts.onChange) opts.onChange(gStr);
        }

        hY.addEventListener('input', syncFromHijri);
        hM.addEventListener('change', syncFromHijri);
        hD.addEventListener('input', syncFromHijri);
        g.addEventListener('change', function () {
            if (g.value) prefillHijriFromGreg(g.value);
        });

        function switchCal(mode) {
            if (mode === 'h') {
                box.classList.remove('d-none');
                g.classList.add('d-none');
                // Drop required from hidden input — browsers refuse to focus
                // hidden invalid required fields and throw a console error.
                if (g.hasAttribute('required')) {
                    g.dataset._wasRequired = '1';
                    g.removeAttribute('required');
                }
            } else {
                box.classList.add('d-none');
                g.classList.remove('d-none');
                if (g.dataset._wasRequired) {
                    g.setAttribute('required', '');
                    delete g.dataset._wasRequired;
                }
            }
        }

        // Initial state.
        if (g.value) {
            prefillHijriFromGreg(g.value);
        } else if (opts.prefillToday) {
            var t = new Date();
            var today = t.getFullYear() + '-' +
                String(t.getMonth() + 1).padStart(2, '0') + '-' +
                String(t.getDate()).padStart(2, '0');
            g.value = today;
            prefillHijriFromGreg(today);
        }
        switchCal(opts.defaultMode || 'h');

        radios.forEach(function (r) {
            if (r.value === (opts.defaultMode || 'h')) r.checked = true;
            r.addEventListener('change', function () {
                if (r.checked) switchCal(r.value);
            });
        });
    }

    root.HijriConv = {
        months: HIJRI_MONTHS_AR,
        gregorianToHijri: gregorianToHijri,
        hijriToGregorian: hijriToGregorian,
        formatHijri: formatHijri,
        formatGregorian: formatGregorian,
        isValidHijri: isValidHijri,
        bindToggle: bindHijriToggle
    };
})(window);
