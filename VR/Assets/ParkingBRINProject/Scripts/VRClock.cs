using UnityEngine;
using TMPro;
using System;
using System.Globalization;

public class VRClock : MonoBehaviour
{
    [Header("References")]
    public TMP_Text clockText;

    [Header("Format")]
    [Tooltip("C# DateTime format string. Examples: HH:mm:ss  |  HH:mm  |  hh:mm tt  |  dd MMM yyyy HH:mm")]
    public string timeFormat = "HH:mm:ss 'WIB'";

    [Tooltip("Locale for month/day names (e.g., id-ID for Indonesian)")]
    public string locale = "id-ID";

    [Header("Update")]
    [Tooltip("How often to refresh the text (seconds). 0.2–1.0 is typical.")]
    public float refreshInterval = 0.5f;

    private float _timer;
    private CultureInfo _culture;

    void Awake()
    {
        if (clockText == null)
            clockText = GetComponentInChildren<TMP_Text>();

        _culture = new CultureInfo(string.IsNullOrEmpty(locale) ? CultureInfo.CurrentCulture.Name : locale);
        UpdateClock(force: true);
    }

    void Update()
    {
        _timer += Time.deltaTime;
        if (_timer >= refreshInterval)
        {
            _timer = 0f;
            UpdateClock();
        }
    }

    private void UpdateClock(bool force = false)
    {
        if (clockText == null) return;

        DateTime nowLocal = DateTime.Now; 
        clockText.text = nowLocal.ToString(timeFormat, _culture);
    }
}
