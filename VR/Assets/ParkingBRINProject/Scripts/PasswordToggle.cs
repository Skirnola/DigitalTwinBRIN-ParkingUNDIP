using UnityEngine;
using TMPro; 
using UnityEngine.UI;

public class PasswordToggle : MonoBehaviour
{
    public TMP_InputField passwordField; 
    public Image toggleImage;           
    public Sprite eyeOpen;           
    public Sprite eyeClosed;          

    private bool isHidden = true;

    public void TogglePasswordVisibility()
    {
        if (isHidden)
        {
            passwordField.contentType = TMP_InputField.ContentType.Standard; 
            toggleImage.sprite = eyeOpen;
            isHidden = false;
        }
        else
        {
            passwordField.contentType = TMP_InputField.ContentType.Password; 
            toggleImage.sprite = eyeClosed;
            isHidden = true;
        }

        passwordField.ForceLabelUpdate();
    }
}
