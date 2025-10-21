using UnityEngine;
using TMPro;
using UnityEngine.UI;

public class PasswordToggleSignup : MonoBehaviour
{
    [Header("Input Fields")]
    public TMP_InputField passwordField;        
    public TMP_InputField confirmPasswordField; 

    [Header("Eye Button Images")]
    public Image passwordToggleImage;          
    public Image confirmToggleImage;            
    public Sprite eyeOpen;                      
    public Sprite eyeClosed;                   

    private bool isPasswordHidden = true;
    private bool isConfirmHidden = true;

    public void TogglePasswordVisibility()
    {
        if (isPasswordHidden)
        {
            passwordField.contentType = TMP_InputField.ContentType.Standard;
            passwordToggleImage.sprite = eyeOpen;
            isPasswordHidden = false;
        }
        else
        {
            passwordField.contentType = TMP_InputField.ContentType.Password;
            passwordToggleImage.sprite = eyeClosed;
            isPasswordHidden = true;
        }
        passwordField.ForceLabelUpdate();
    }

    public void ToggleConfirmPasswordVisibility()
    {
        if (isConfirmHidden)
        {
            confirmPasswordField.contentType = TMP_InputField.ContentType.Standard;
            confirmToggleImage.sprite = eyeOpen;
            isConfirmHidden = false;
        }
        else
        {
            confirmPasswordField.contentType = TMP_InputField.ContentType.Password;
            confirmToggleImage.sprite = eyeClosed;
            isConfirmHidden = true;
        }
        confirmPasswordField.ForceLabelUpdate();
    }
}
