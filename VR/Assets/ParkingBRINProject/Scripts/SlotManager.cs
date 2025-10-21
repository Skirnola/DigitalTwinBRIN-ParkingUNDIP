using UnityEngine;

public class SlotManager : MonoBehaviour
{
    public GameObject smallCar;
    public GameObject mediumCar;
    public GameObject bigCar;

    public void SetCarState(bool isOccupied, string size)
    {
        // Hide all cars first
        if (smallCar != null) smallCar.SetActive(false);
        if (mediumCar != null) mediumCar.SetActive(false);
        if (bigCar != null) bigCar.SetActive(false);

        if (isOccupied)
        {
            switch (size)
            {
                case "Small":
                    if (smallCar != null) smallCar.SetActive(true);
                    break;
                case "Medium":
                    if (mediumCar != null) mediumCar.SetActive(true);
                    break;
                case "Big":
                    if (bigCar != null) bigCar.SetActive(true);
                    break;
                default:
                    Debug.LogWarning($"[SlotManager] Unknown size: {size} at {gameObject.name}");
                    break;
            }
        }
    }
}
